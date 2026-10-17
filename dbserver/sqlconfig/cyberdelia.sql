-- CYBERDELIA seed :: run against the 'gibson' database

DROP USER IF EXISTS cyberdelia;
CREATE USER cyberdelia WITH PASSWORD 'w4r3z';

DROP TABLE IF EXISTS graffiti;
CREATE TABLE graffiti (
  id      SERIAL PRIMARY KEY,
  handle  VARCHAR(64),
  message TEXT
);

-- least privilege: only what the app actually does (insert + read the wall)
GRANT SELECT, INSERT ON TABLE graffiti TO cyberdelia;
GRANT USAGE ON SEQUENCE graffiti_id_seq TO cyberdelia;

-- seed the wall
INSERT INTO graffiti (handle, message) VALUES
  ('Z3r0C00l',      'Hack the planet!'),
  ('Ac1dBurn',      'Mess with the best, die like the rest.'),
  ('J0shua',        'Shall we play a game?'),
  ('CrashOverride', 'There is no right and wrong. Only fun and boring.'),
  ('Th3Pl4gu3',     'The cake is a lie.');