SELECT owner, name, type, referenced_owner, referenced_name, referenced_type, dependency_type
FROM all_dependencies
WHERE referenced_owner='MC'
  AND referenced_name IN ('CESTOVNE_PR_L','CESTOVNE_PR_O','D_CPR_L','D_CPR_O')
ORDER BY referenced_name, owner, name, type;
