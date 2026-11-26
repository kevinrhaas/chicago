// SPDX-License-Identifier: GPL-3.0-or-later
/** One nearby face page, shared by every wearer. The crowd sheet always remains available.
 * Loading and decoded pages share the same slot: walking through a crowd cannot queue an
 * unbounded collection of images or re-upload an evicted texture through an old material.
 * The renderer submits only visible heads; the nearest page wins with a little hysteresis.
 */
export const PHOTO_FACE_BUDGET = Object.freeze({ faces: 256, crowdBytes: 5_600_000,
  pageBytes: 5_600_000, pageEdge: 1024, nearM: 6, residentPages: 1 });

export class PhotoFacePages {
  constructor({ load, dispose, schedule = fn => setTimeout(fn, 0), now = () => Date.now() }) {
    this.load = load; this.release = dispose; this.schedule = schedule; this.now = now;
    this.requests = new Map(); this.retry = new Map(); this.current = null;
    this.pending = null; this.wanted = null; this.scheduled = false; this.closed = false;
  }
  demand(page, distance) {
    if (this.closed || !page?.url || !Number.isFinite(distance) || distance < 0 || distance > PHOTO_FACE_BUDGET.nearM
        || !(page.bytes > 0 && page.bytes <= PHOTO_FACE_BUDGET.pageBytes)) return;
    const previous = this.requests.get(page.url);
    if (!previous || distance < previous.distance) this.requests.set(page.url, { page, distance });
    if (this.schedule && !this.scheduled) {
      this.scheduled = true;
      this.schedule(() => { this.scheduled = false; this.flush(); });
    }
  }
  flush() {
    if (this.closed) return;
    const requests = [...this.requests.values()]; this.requests.clear();
    const score = r => r.distance * (r.page.url === this.current?.page.url ? .85 : 1);
    requests.sort((a, b) => score(a) - score(b) || a.page.url.localeCompare(b.page.url));
    this.wanted = requests[0]?.page ?? null;
    this.pump();
  }
  pump() {
    if (this.closed || this.pending || !this.wanted || this.current?.page.url === this.wanted.url) return;
    if (this.current) { this.release(this.current.texture); this.current = null; }
    const page = this.wanted;
    if ((this.retry.get(page.url) ?? 0) > this.now()) return;
    const task = this.pending = { page, promise: null };
    task.promise = Promise.resolve().then(() => this.load(page)).then(texture => {
      this.pending = null;
      if (this.closed || this.wanted?.url !== page.url) this.release(texture);
      else { this.current = { page, texture }; this.retry.delete(page.url); }
      this.pump();
    }, () => {
      this.pending = null; this.retry.set(page.url, this.now() + 30_000);
      this.pump();
    });
  }
  get(url) { return this.current?.page.url === url ? this.current.texture : null; }
  async ready() { while (this.pending) await this.pending.promise; }
  stats() {
    return { residentPages: this.current ? 1 : 0, pendingPages: this.pending ? 1 : 0,
      residentBytes: this.current?.page.bytes ?? 0, pendingBytes: this.pending?.page.bytes ?? 0,
      pageLimit: PHOTO_FACE_BUDGET.residentPages, byteLimit: PHOTO_FACE_BUDGET.pageBytes,
      page: this.current?.page.url ?? null };
  }
  dispose() {
    this.closed = true; this.wanted = null; this.requests.clear(); this.retry.clear();
    if (this.current) this.release(this.current.texture);
    this.current = null;
  }
}
