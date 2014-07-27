drop tables if exists suspect_ips;
create table suspect_ips(
    id integer primary key autoincrement,
    ip text not null unique,
    hostname text not null,
    latitude real not null,
    longitude real not null,
    country text not null collate nocase,
    date text not null
);
