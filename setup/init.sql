CREATE DATABASE uk_staff_locations;
\connect uk_staff_locations;
CREATE SCHEMA dit;
CREATE TABLE dit.uk_staff_locations (
    location_code varchar(255) PRIMARY KEY,
    location_name varchar(255),
    city varchar(255)
);

INSERT INTO dit.uk_staff_locations (location_code, location_name, city)
VALUES ('123', 'Test Location', 'London');