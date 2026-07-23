create extension if not exists "pgcrypto";

create table if not exists resumes (
    id uuid primary key default gen_random_uuid(),
    original_filename text not null,
    file_url text,
    full_name text,
    email text,
    phone text,
    parsed_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists skills (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid not null references resumes(id) on delete cascade,
    skill_name text not null,
    created_at timestamptz not null default now()
);

create table if not exists education (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid not null references resumes(id) on delete cascade,
    degree text,
    branch text,
    college text,
    university text,
    cgpa text,
    percentage text,
    graduation_year text,
    current_status text,
    created_at timestamptz not null default now()
);

create table if not exists experience (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid not null references resumes(id) on delete cascade,
    company_name text,
    job_title text,
    internship boolean default false,
    start_date text,
    end_date text,
    duration text,
    responsibilities jsonb default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists projects (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid not null references resumes(id) on delete cascade,
    project_title text,
    technologies_used jsonb default '[]'::jsonb,
    description text,
    github_link text,
    live_demo_link text,
    created_at timestamptz not null default now()
);

create table if not exists certifications (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid not null references resumes(id) on delete cascade,
    certificate_name text,
    issuing_organization text,
    completion_date text,
    created_at timestamptz not null default now()
);

create table if not exists awards (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid not null references resumes(id) on delete cascade,
    title text,
    type text,
    created_at timestamptz not null default now()
);

create index if not exists idx_resumes_email on resumes(email);
create index if not exists idx_resumes_full_name on resumes(full_name);
create index if not exists idx_resumes_parsed_json on resumes using gin(parsed_json);
create index if not exists idx_skills_skill_name on skills(skill_name);
