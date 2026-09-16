-- Reverse proposal retention trace
-- Grain: One OBJD line
-- Proves: Current RID_N matches and missing current proposal
-- Does not prove: Universal historical 1:1 relationship or corruption
-- Fan-out: Proposal PK lookup; multiple lines may repeat proposal.
-- MC only; SQL Navigator 5.5.4.847; Oracle version unknown.
SELECT O.RID_O, O.ID_R, O.RID_N, N.RID AS current_proposal_rid
FROM MC.OBJD_O O
LEFT JOIN MC.OBJ_D_NAVRH N ON N.RID = O.RID_N
WHERE O.RID_O = :p_document_rid;
