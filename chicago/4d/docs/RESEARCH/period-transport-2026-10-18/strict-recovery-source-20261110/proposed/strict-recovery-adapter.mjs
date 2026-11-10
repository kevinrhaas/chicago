// SPDX-License-Identifier: GPL-3.0-or-later
/** Outside-app contract study. No current scene, physical boarding, motion or UI binding.
 * Preparation may wait; camera/visitor commit, compensation and lease release are
 * synchronous acknowledged transactions. Unsupported ports refuse before recovery.
 */
export const STRICT_RECOVERY_CONTRACT = 'outside-app/strict-recovery-v1';
const abort = () => Object.assign(Error('Superseded recovery owner'), { name: 'AbortError' });
const thenable = value => value && typeof value.then === 'function';
function synchronous(fn, ...args) {
  const value = fn(...args);
  if (thenable(value)) { value.catch?.(() => {}); throw Error('Unsupported asynchronous recovery commit/verification'); }
  return value;
}
function waiter(promise, signal) {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(abort());
  return new Promise((resolve, reject) => {
    const off = () => signal.removeEventListener('abort', stop);
    const stop = () => { off(); reject(abort()); };
    signal.addEventListener('abort', stop, { once: true });
    promise.then(value => { off(); resolve(value); }, error => { off(); reject(error); });
  });
}

export function createStrictRecoveryAdapter({ base, ports, getOwner }) {
  const required = ['isStopped', 'captureLeases', 'prepare', 'verifyHeld', 'commit',
    'verifyRecovered', 'releaseLeases', 'verifyReleased', 'compensate'];
  if (!base || typeof getOwner !== 'function' || ports?.commitKind !== 'synchronous-compensated-v1'
    || required.some(key => typeof ports[key] !== 'function')) throw Error('Unsupported strict recovery ports');
  for (const key of required.filter(key => key !== 'prepare'))
    if (ports[key].constructor.name === 'AsyncFunction') throw Error('Unsupported asynchronous recovery port: ' + key);
  const stops = new WeakMap(), leases = new WeakMap();
  const events = [];
  const stopped = () => {
    const speed = base.vehicleStatus()?.speed_m_s;
    return Number.isFinite(speed) && Math.abs(speed) <= 1e-5 && synchronous(ports.isStopped) === true;
  };
  function stopVehicle({ signal, immediate = false, retryOwned = false } = {}) {
    const owner = getOwner();
    if (!owner || typeof owner !== 'object') return Promise.reject(Error('No owned seat for strict stop'));
    let entry = stops.get(owner);
    // Only an explicit later recovery command may retry a settled rejection.
    // Pending operations are never replaced, including when their waiter aborts.
    if (!entry || (retryOwned && entry.state === 'rejected')) {
      entry = { state: 'pending', promise: null };
      const own = entry;
      own.promise = Promise.resolve().then(() => base.stopVehicle({ immediate })).then(result => {
        if (result?.completed !== true || result?.finalNeutral !== true || !stopped())
          throw Error('Stop has not verified final neutral');
        own.state = 'fulfilled'; events.push('stop-verified'); return result;
      }).catch(error => { own.state = 'rejected'; throw error; });
      own.promise.catch(() => {}); stops.set(owner, own); events.push('stop-owned');
    }
    return waiter(entry.promise.then(result => {
      if (!stopped()) throw Error('Previously stopped provider is no longer neutral');
      return result;
    }), signal);
  }
  async function recoverStrict(ctx) {
    const check = () => { if (!ctx.isCurrent() || getOwner() !== ctx.token) throw abort(); };
    check();
    let lease = leases.get(ctx.token);
    if (!lease) {
      lease = synchronous(ports.captureLeases, ctx);
      if (!lease || lease.ownerToken !== ctx.token
        || !['visitor', 'camera', 'person', 'model', 'attached'].every(key => Object.hasOwn(lease, key))
        || ['visitor', 'camera', 'model'].some(key => !lease[key] || typeof lease[key] !== 'object'))
        throw Error('Unsupported complete ownership snapshot');
      leases.set(ctx.token, lease);
    }
    const held = () => synchronous(ports.verifyHeld, lease, ctx) === true;
    if (!held()) throw Error('Owned attachment/leases are not verified; recovery refused');
    ctx.retained(lease.attached === true);
    await stopVehicle({ immediate: true, retryOwned: ctx.retry === true }); check();
    if (!held()) throw Error('Stop lost owned attachment/leases; recovery refused');
    let plan, intent;
    do {
      intent = ctx.intentRevision();
      plan = await ports.prepare({ ...ctx, lease }); check();
    } while (intent !== ctx.intentRevision()); // Cancellation replaced only a nonmutating plan.
    if (plan?.prepared !== true || plan?.compensationReady !== true || plan?.ownerToken !== ctx.token || !held())
      throw Error('Recovery plan cannot safely commit and compensate');
    let active = true;
    const transaction = { ...ctx, lease, isCurrent: () => active && ctx.isCurrent() && getOwner() === ctx.token };
    try {
      // No await between commit, independent state verification and lease release.
      // A mutate-then-throw is compensated before another animation frame can run.
      const receipt = synchronous(ports.commit, plan, transaction);
      check();
      if (intent !== ctx.intentRevision()) throw Error('Recovery intent changed during commit');
      if (receipt?.committed !== true || receipt?.ownerToken !== ctx.token
        || synchronous(ports.verifyRecovered, receipt, plan, transaction) !== true)
        throw Error('Recovery commit is not independently verified');
      events.push('recovery-verified');
      const released = synchronous(ports.releaseLeases, receipt, plan, transaction);
      check();
      if (intent !== ctx.intentRevision()) throw Error('Recovery intent changed during release');
      if (released?.released !== true || released?.ownerToken !== ctx.token
        || synchronous(ports.verifyReleased, released, plan, transaction) !== true)
        throw Error('Person/model/visitor/camera release not acknowledged');
      events.push('leases-released'); active = false;
      return { committed: true, verified: true, token: ctx.token };
    } catch (error) {
      active = false; // Deferred work from a refused transaction loses its token.
      if (!ctx.isCurrent() || getOwner() !== ctx.token) throw abort();
      const compensation = synchronous(ports.compensate, plan, { ...ctx, lease, error });
      if (compensation?.compensated !== true || compensation?.ownerToken !== ctx.token || !held())
        throw Error('Recovery failed; compensation/attachment retention is unverified');
      ctx.retained(lease.attached === true); events.push('compensation-verified');
      if (intent !== ctx.intentRevision()) return recoverStrict(ctx);
      throw Error('Recovery blocked after compensated failure: ' + error.message);
    }
  }
  return { ...base, strictRecoveryContract: STRICT_RECOVERY_CONTRACT, recoverStrict, stopVehicle,
    async startVehicle(options) {
      const owner = getOwner(), pending = owner && stops.get(owner);
      if (pending && pending.state !== 'fulfilled') throw Error('Owned stop is pending or failed');
      if (owner) stops.delete(owner);
      return base.startVehicle(options);
    },
    recoveryReading: () => [...events],
  };
}
