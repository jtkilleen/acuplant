drop table if exists plants;
create table plants(
	id integer primary key autoincrement,
	commonname text not null,
	sciname text not null
);

drop table if exists users;
create table users(
	id integer primary key autoincrement,
	username varchar(255) not null,
	password varchar(255) not null
);
