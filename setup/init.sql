CREATE DATABASE uk_staff_locations;
\connect uk_staff_locations;
CREATE SCHEMA dit;
CREATE TABLE dit.uk_staff_locations (
    location_code varchar(255) PRIMARY KEY,
    location_name varchar(255),
    city varchar(255),
    organisation varchar(255),
    building_name varchar(255)
);

INSERT INTO dit.uk_staff_locations (location_code, location_name, city, organisation, building_name)
VALUES
    ('123', 'Test Location 1, London', 'London', 'Department for Business and Trade', 'Test Location 1'),
    ('456', 'Test Location 2, London', 'London', 'Department for Business and Trade', 'Test Location 2'),
    ('789', 'Test Location 3, London', 'London', 'Department for Business and Trade', 'Test Location 3'),
    ('987', 'Test Location 4, Darlington', 'Darlington', 'Department for Business and Trade', 'Test Location 4'),
    ('645', 'Test Location 5, Cardiff', 'Cardiff', 'Department for Business, Energy and Industrial Strategy', 'Test Location 5'),
    ('321', 'Test Location 6, Cardiff', 'Cardiff', 'Department for Business and Trade', 'Test Location 6');