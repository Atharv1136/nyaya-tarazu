-- ============================================================
-- 001_legal_sections.sql
-- Nyaya Tarazu — Legal Corpus Schema
-- ============================================================
-- Run order: apply once against the Supabase project.
-- Embedding dimension: 768 (Gemini text-embedding-004, MRL)
-- Vector index: HNSW with cosine distance
-- ============================================================

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Main table
create table if not exists legal_sections (
  id                 uuid        primary key default gen_random_uuid(),

  -- Source provenance
  source_file        text        not null,   -- original PDF filename, e.g. "IPC_1860.pdf"
  act_name           text        not null,   -- e.g. "Indian Penal Code, 1860"
  section_number     text,                   -- e.g. "302", "103", "304B"
  section_title      text,                   -- e.g. "Punishment for murder"
  page_number        integer,
  bounding_box       jsonb,                  -- {x1, y1, x2, y2} in PDF points

  -- Legal classification
  code_era           text        check (code_era in ('old', 'new')),
  --   'old' → IPC 1860 / CrPC 1973 / IEA 1872
  --   'new' → BNS 2023 / BNSS 2023 / BSA 2023

  cross_references   text[],                 -- e.g. ["IPC 302", "IPC 303"]

  -- Extraction metadata
  extraction_method  text        default 'heading_split',
  --   'heading_split'          → structural extraction from JSON tree
  --   'fallback_sliding_window' → scanned PDF fallback

  -- Content
  chunk_text         text        not null,

  -- Vector embedding (Gemini text-embedding-004, 768-dim MRL)
  embedding          vector(768),

  created_at         timestamptz default now()
);

-- 3. HNSW vector index (cosine distance)
--    m=16, ef_construction=64 are good defaults for corpora of this size.
create index if not exists legal_sections_embedding_idx
  on legal_sections
  using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

-- 4. Scalar metadata indexes (for filtered vector search by era or act)
create index if not exists legal_sections_code_era_idx
  on legal_sections (code_era);

create index if not exists legal_sections_act_name_idx
  on legal_sections (act_name);

create index if not exists legal_sections_section_number_idx
  on legal_sections (section_number);

-- 5. match_legal_sections — RPC function used by the Python client
--    Performs cosine similarity search with optional era filter.
create or replace function match_legal_sections(
  query_embedding   vector(768),
  match_threshold   float   default 0.7,
  match_count       int     default 5,
  filter_era        text    default null
)
returns table (
  id               uuid,
  act_name         text,
  section_number   text,
  section_title    text,
  code_era         text,
  source_file      text,
  page_number      integer,
  cross_references text[],
  chunk_text       text,
  similarity       float
)
language plpgsql
as $$
begin
  return query
  select
    ls.id,
    ls.act_name,
    ls.section_number,
    ls.section_title,
    ls.code_era,
    ls.source_file,
    ls.page_number,
    ls.cross_references,
    ls.chunk_text,
    (1.0 - (ls.embedding <=> query_embedding))::float as similarity
  from legal_sections ls
  where
    ls.embedding is not null
    and (filter_era is null or ls.code_era = filter_era)
    and (1.0 - (ls.embedding <=> query_embedding)) >= match_threshold
  order by ls.embedding <=> query_embedding
  limit match_count;
end;
$$;
