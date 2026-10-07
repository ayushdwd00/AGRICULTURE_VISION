-- =============================================================================
-- AgriVision: Supabase PostgreSQL Seed Data
-- Demo data for Module 5 (Product Registry) and Module 7 (Equipment Rental)
--
-- SECURITY NOTE:
-- Plaintext passwords are NOT stored in this SQL script.
-- Passwords below are precomputed salted PBKDF2-SHA256 hashes matching
-- AgriVision's exact algorithm:
--   - PBKDF2 with SHA-256
--   - 120,000 iterations
--   - Salted digest in format: pbkdf2_sha256$iterations$salt$hex_digest
--
-- Demo credentials:
--   farmer_demo / farmer123
--   owner_demo  / owner123
--
-- For dynamic seeding with custom passwords or random salts, run the Python
-- repository functions: `backend.database.UserRepository.create(...)`.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Demo Products (Module 5: Product Verifier Registry)
-- -----------------------------------------------------------------------------
INSERT INTO products (code, product_name, manufacturer, batch, expiry, status, product_type, registered_on)
VALUES
    ('AGV-1001', 'AgriShield Mancozeb 75% WP', 'Demo Agro Chemicals Pvt Ltd', 'MCZ-2405', '2027-04-30', 'Verified', 'Fungicide', NOW()),
    ('AGV-1002', 'AgriShield Neem Oil 1500 ppm', 'Demo Agro Chemicals Pvt Ltd', 'NEM-2312', '2026-12-31', 'Verified', 'Bio-pesticide', NOW()),
    ('AGV-1003', 'GreenGrow Urea 46% N', 'Demo Fertiliser Cooperative', 'URE-2501', '2028-06-30', 'Verified', 'Fertilizer', NOW()),
    ('AGV-1004', 'GreenGrow DAP 18-46-0', 'Demo Fertiliser Cooperative', 'DAP-2410', '2028-01-31', 'Verified', 'Fertilizer', NOW()),
    ('AGV-1005', 'CropCare Imidacloprid 17.8% SL', 'Demo Crop Science Ltd', 'IMD-2308', '2026-03-15', 'Recalled', 'Insecticide', NOW()),
    ('AGV-1006', 'CropCare Glyphosate 41% SL', 'Demo Crop Science Ltd', 'GLY-2201', '2025-11-30', 'Verified', 'Herbicide', NOW()),
    ('AGV-1007', 'SoilBoost Bio-fertiliser (Azotobacter)', 'Demo Bio Inputs', 'BIO-2502', '2027-05-31', 'Verified', 'Bio-fertilizer', NOW()),
    ('AGV-1008', 'SoilBoost Zinc Sulphate 21%', 'Demo Bio Inputs', 'ZNS-2411', '2029-02-28', 'Verified', 'Micronutrient', NOW()),
    ('AGV-1009', 'HarvestPlus MOP (Muriate of Potash)', 'Demo Fertiliser Cooperative', 'MOP-2409', '2028-09-30', 'Verified', 'Fertilizer', NOW()),
    ('AGV-1010', 'HarvestPlus Sulphur 90% WDG', 'Demo Fertiliser Cooperative', 'SUL-2306', '2027-08-31', 'Suspended', 'Fungicide', NOW())
ON CONFLICT (code) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. Demo Users (Module 7: Equipment Rental Marketplace)
-- Password hashes generated with pbkdf2_sha256, 120,000 iterations
-- -----------------------------------------------------------------------------
INSERT INTO users (username, password_hash, role, full_name, phone, location, created_at)
VALUES
    (
        'farmer_demo',
        'pbkdf2_sha256$120000$demo_farmer_salt_2026$8fd2eef52c4acaa257ec01bf95f6e4940b876c75731f858eecfedd1902c5cc14',
        'farmer',
        'Ramesh Kumar (demo farmer)',
        '9000000001',
        'Varanasi',
        NOW()
    ),
    (
        'owner_demo',
        'pbkdf2_sha256$120000$demo_owner_salt_2026$e9f5a27d1a4286cff73c1904a6d0c77ba8d9cf1280631858a04fcff95741f816',
        'owner',
        'Suresh Singh (demo machine owner)',
        '9000000002',
        'Varanasi',
        NOW()
    )
ON CONFLICT (username) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. Demo Machines (Module 7: Listings associated with owner_demo)
-- -----------------------------------------------------------------------------
INSERT INTO machines (name, machine_type, hourly_rate, daily_rate, location, owner_id, description, available, created_at, updated_at)
SELECT
    m.name,
    m.machine_type,
    m.hourly_rate,
    m.daily_rate,
    m.location,
    u.id AS owner_id,
    m.description,
    TRUE,
    NOW(),
    NOW()
FROM (
    VALUES
        (
            'Mahindra 275 DI Tractor',
            'Tractor',
            800.00,
            5200.00,
            'Varanasi',
            '42 HP tractor with plough - suitable for 1-5 acre fields.'
        ),
        (
            'Kubota Combine Harvester',
            'Harvester',
            2500.00,
            15000.00,
            'Chandauli',
            'Self-propelled harvester for wheat and paddy.'
        ),
        (
            'Rotavator (6 feet)',
            'Rotavator',
            600.00,
            3800.00,
            'Varanasi',
            'Soil preparation attachment, needs a 35 HP+ tractor.'
        ),
        (
            'Power Sprayer (battery)',
            'Sprayer',
            150.00,
            900.00,
            'Ramnagar',
            '16 litre battery sprayer for pesticide / fungicide application.'
        )
) AS m(name, machine_type, hourly_rate, daily_rate, location, description)
CROSS JOIN (
    SELECT id FROM users WHERE username = 'owner_demo' LIMIT 1
) u
WHERE NOT EXISTS (
    SELECT 1 FROM machines WHERE name = m.name AND owner_id = u.id
);
