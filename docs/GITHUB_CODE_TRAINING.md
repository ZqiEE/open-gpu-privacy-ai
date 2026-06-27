# GitHub Code Training

GitHub Repo Understanding is the first Ailovanta-Code training capability.

## Capabilities

Ailovanta-Code should learn to:

- read repository structure
- summarize project architecture
- detect languages and frameworks
- detect test commands
- detect CI configuration
- read error logs
- map an issue to a repair plan
- generate a patch
- generate a pull request summary
- continue fixing after a failed test

## Authorized sources

Training data may come from:

- authorized GitHub repositories
- investor-authorized repositories
- partner-authorized repositories
- user-connected repositories
- permissive open-source repositories
- Ailovanta's own issues, commits, and tests

Every source must bind to a Rights Proof Registry record.

## Sample shape

```json
{
  "schema_version": "ailovanta.github_code_sample.v1",
  "repo_id": "repo_xxx",
  "rights_id": "rights_xxx",
  "language": "python",
  "framework": "fastapi",
  "issue": "Fix failing test",
  "repo_tree": "...",
  "relevant_files": [],
  "error_log": "...",
  "expected_patch": "...",
  "tests": [],
  "ci_result": "pass"
}
```
