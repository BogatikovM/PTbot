FROM postgres:15

WORKDIR /db

COPY init.sql /docker-entrypoint-initdb.d/

RUN mkdir /db/archive

RUN chown -R postgres:postgres /db
