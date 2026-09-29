-- Grain: exactly one OBCH_PARTNERI row when :partner_id exists in MC.
-- Limit: current master snapshot; not historical partner truth.
SELECT p.*
FROM mc.obch_partneri p
WHERE p.id = :partner_id;
