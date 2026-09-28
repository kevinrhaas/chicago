-- Chicago Building Atlas — notes database (Supabase / Postgres 15+).
--
-- Paste this whole file into the SQL editor of the notes project and run it.
-- Safe to run again: every statement is create-or-replace / if-not-exists.
--
-- THE ACCESS MODEL
--   • Anyone can READ the notes that are not archived (no IP / browser shown).
--   • Only an EDITOR can add, archive or restore a note, and only an editor sees
--     archived notes and the IP / browser / device stamped on each one.
--   • An editor is a row in notes_private.editors. Their personal edit link is
--     https://chicago.polecat.live/?notes=<token>; the database keeps only the
--     token's SHA-256, never the token itself. Create one with
--         select notes_private.add_editor('Bill Tyre');
--     (it returns the token ONCE — see README.md in this folder).
--   • The browser only ever holds the project's publishable key. Tables live in a
--     schema the API does not expose, with RLS on and no grants; the four
--     public.notes_* functions below are the only way in.

create schema if not exists notes_private;
revoke all on schema notes_private from public;
revoke all on schema notes_private from anon, authenticated;

create table if not exists notes_private.editors (
  id          uuid primary key default gen_random_uuid(),
  name        text not null check (char_length(name) between 1 and 80),
  token_hash  text not null unique,
  active      boolean not null default true,
  created_at  timestamptz not null default now()
);

create table if not exists notes_private.notes (
  id           uuid primary key default gen_random_uuid(),
  site         text not null check (char_length(site) <= 120),
  page         text not null check (char_length(page) <= 120),
  target       text not null check (char_length(target) <= 300),
  target_label text check (char_length(target_label) <= 300),
  body         text not null check (char_length(body) between 1 and 4000),
  editor_id    uuid references notes_private.editors(id),
  author       text,
  path         text check (char_length(path) <= 500),
  device       text check (char_length(device) <= 64),
  ip           text,
  ua           text,
  created_at   timestamptz not null default now(),
  archived_at  timestamptz,
  archived_by  text
);
create index if not exists notes_page_idx on notes_private.notes (site, page, created_at desc);

alter table notes_private.editors enable row level security;
alter table notes_private.notes   enable row level security;
revoke all on all tables in schema notes_private from public, anon, authenticated;

-- ---- helpers (not callable through the API) --------------------------------

create or replace function notes_private.token_hash(p_token text) returns text
language sql immutable set search_path = '' as $$
  select encode(pg_catalog.sha256(pg_catalog.convert_to(coalesce(p_token, ''), 'UTF8')), 'hex')
$$;

-- The editor a token belongs to, or NULL. A wrong token costs a short pause so
-- guessing is slow; an absent token (a reader) costs nothing.
create or replace function notes_private.editor_for(p_token text) returns notes_private.editors
language plpgsql security definer set search_path = '' as $$
declare e notes_private.editors;
begin
  if p_token is null or p_token = '' then return null; end if;
  select * into e from notes_private.editors
   where token_hash = notes_private.token_hash(p_token) and active;
  if e.id is null then perform pg_catalog.pg_sleep(0.4); end if;
  return e;
end $$;

create or replace function notes_private.req_header(p_name text) returns text
language plpgsql stable set search_path = '' as $$
begin
  return pg_catalog.current_setting('request.headers', true)::json ->> p_name;
exception when others then
  return null; -- header stamping is best-effort; never block a write
end $$;

-- Run by the OWNER in the SQL editor. Returns the new editor's token once.
create or replace function notes_private.add_editor(p_name text) returns text
language plpgsql security definer set search_path = '' as $$
declare t text := replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
begin
  insert into notes_private.editors (name, token_hash) values (p_name, notes_private.token_hash(t));
  return t;
end $$;

revoke all on all functions in schema notes_private from public, anon, authenticated;

-- ---- the API: four functions ------------------------------------------------

drop function if exists public.notes_list(text, text, text);
create function public.notes_list(p_site text, p_page text, p_token text default null)
returns table (
  id uuid, target text, target_label text, body text, author text, created_at timestamptz,
  archived_at timestamptz, archived_by text, ip text, ua text, device text, path text
)
language plpgsql stable security definer set search_path = '' as $$
#variable_conflict use_column
declare e notes_private.editors := notes_private.editor_for(p_token);
begin
  if p_token is not null and p_token <> '' and e.id is null then
    raise exception 'notes: edit link not recognised' using errcode = '28P01';
  end if;
  return query
    select n.id, n.target, n.target_label, n.body, n.author, n.created_at,
           n.archived_at,
           case when e.id is not null then n.archived_by end,
           case when e.id is not null then n.ip end,
           case when e.id is not null then n.ua end,
           case when e.id is not null then n.device end,
           n.path
      from notes_private.notes n
     where n.site = p_site and n.page = p_page
       and (e.id is not null or n.archived_at is null)
     order by n.created_at desc
     limit 2000;
end $$;

create or replace function public.notes_whoami(p_token text) returns json
language plpgsql stable security definer set search_path = '' as $$
declare e notes_private.editors := notes_private.editor_for(p_token);
begin
  if e.id is null then
    raise exception 'notes: edit link not recognised' using errcode = '28P01';
  end if;
  return json_build_object('name', e.name);
end $$;

drop function if exists public.notes_add(text, text, text, text, text, text, text, text);
create function public.notes_add(
  p_token text, p_site text, p_page text, p_target text, p_label text, p_body text,
  p_path text default null, p_device text default null
) returns table (
  id uuid, target text, target_label text, body text, author text, created_at timestamptz,
  archived_at timestamptz, archived_by text, ip text, ua text, device text, path text
)
language plpgsql security definer set search_path = '' as $$
#variable_conflict use_column
declare e notes_private.editors := notes_private.editor_for(p_token);
begin
  if e.id is null then
    raise exception 'notes: edit link not recognised' using errcode = '28P01';
  end if;
  return query
    insert into notes_private.notes as n
      (site, page, target, target_label, body, editor_id, author, path, device, ip, ua)
    values (p_site, p_page, p_target, p_label, btrim(p_body), e.id, e.name, p_path, p_device,
            nullif(btrim(split_part(coalesce(notes_private.req_header('x-forwarded-for'), ''), ',', 1)), ''),
            left(notes_private.req_header('user-agent'), 300))
    returning n.id, n.target, n.target_label, n.body, n.author, n.created_at,
              n.archived_at, n.archived_by, n.ip, n.ua, n.device, n.path;
end $$;

-- Archive (p_archive = true) or restore (false). Nothing is ever deleted.
drop function if exists public.notes_archive(text, uuid, boolean);
create function public.notes_archive(p_token text, p_id uuid, p_archive boolean default true)
returns table (
  id uuid, target text, target_label text, body text, author text, created_at timestamptz,
  archived_at timestamptz, archived_by text, ip text, ua text, device text, path text
)
language plpgsql security definer set search_path = '' as $$
#variable_conflict use_column
declare e notes_private.editors := notes_private.editor_for(p_token);
begin
  if e.id is null then
    raise exception 'notes: edit link not recognised' using errcode = '28P01';
  end if;
  return query
    update notes_private.notes as n
       set archived_at = case when p_archive then now() end,
           archived_by = case when p_archive then e.name end
     where n.id = p_id
    returning n.id, n.target, n.target_label, n.body, n.author, n.created_at,
              n.archived_at, n.archived_by, n.ip, n.ua, n.device, n.path;
end $$;

revoke all on function public.notes_list(text, text, text)       from public;
revoke all on function public.notes_whoami(text)                 from public;
revoke all on function public.notes_add(text, text, text, text, text, text, text, text) from public;
revoke all on function public.notes_archive(text, uuid, boolean) from public;
grant execute on function public.notes_list(text, text, text)       to anon, authenticated;
grant execute on function public.notes_whoami(text)                 to anon, authenticated;
grant execute on function public.notes_add(text, text, text, text, text, text, text, text) to anon, authenticated;
grant execute on function public.notes_archive(text, uuid, boolean) to anon, authenticated;

notify pgrst, 'reload schema';
