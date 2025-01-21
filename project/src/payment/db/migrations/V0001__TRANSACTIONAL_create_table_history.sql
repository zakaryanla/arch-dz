CREATE SCHEMA IF NOT EXISTS payment;

CREATE TABLE payment.users_balance (
    userid UUID NOT NULL,
    tr_guid UUID NOT NULL,
    sum integer NOT NULL,
    created timestamp DEFAULT now()
);

CREATE TABLE payment.subscriptions (
    subscription character varying(40),
    lvl integer NOT NULL,
    sum integer NOT NULL
);
 
insert into payment.subscriptions values ('Essential', 1, 100);
insert into payment.subscriptions values ('Extra', 2, 150);
insert into payment.subscriptions values ('Premium', 3, 200);	

CREATE TABLE payment.users_subscription(
    userid UUID NOT NULL,
    subscription character varying(40),
    date_before date NOT NULL,
    created timestamp DEFAULT now()
);

CREATE TABLE payment.users_books(
    userid UUID NOT NULL,
    bookid UUID NOT NULL,
    created timestamp DEFAULT now()
);