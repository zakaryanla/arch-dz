CREATE SEQUENCE public.userid
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.users (
    id integer DEFAULT nextval('public.userid'::regclass),
    username character varying(40) NOT NULL,
    firstname character varying(40),
    lastname character varying(40),
    email character varying(40),
    phone character varying(40)
);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_id_key UNIQUE (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);
