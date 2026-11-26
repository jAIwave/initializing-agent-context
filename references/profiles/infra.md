# Profile: Infrastructure (Terraform, Ansible, Kubernetes, Docker)

## Detect

- Terraform: `*.tf`, `*.tfvars`, `.terraform.lock.hcl`, `backend.tf`
- Terragrunt: `terragrunt.hcl`
- Ansible: `ansible.cfg`, `playbooks/`, `roles/`, `inventory/`
- Kubernetes: `k8s/`, `manifests/`, `kustomization.yaml`, `Chart.yaml`
- Docker: `Dockerfile`, `compose.yaml`, `.dockerignore`
- CI deploy workflows and `deploy/` scripts

## Commands to verify (read-only first)

```bash
terraform fmt -check -recursive
terraform validate
terraform plan -out=tfplan        # plan only; review before apply
terraform show -json tfplan
ansible-lint
ansible-playbook --syntax-check playbook.yml
kubectl diff -f k8s/
helm lint chart/
helm template chart/
docker compose config
```

Never run `terraform apply`, `terraform destroy`, `kubectl apply`, or a deploy
script during discovery.

## Common invariants

- `apply`/`destroy` require an approved plan and the correct workspace.
- State is remote and locked; never edit state by hand.
- Secrets come from a secret manager; not from `.tfvars` in git.
- Production and staging are separate workspaces/accounts/contexts.
- Images are pinned by digest or immutable tag, not `latest`.
- Rollback is documented before the first deploy.
- Drift is detected by plan, not by manual inspection.

## Hazards

- The current kubeconfig/cloud context may be production.
- `.terraform/` and plan files contain sensitive data.
- `terraform plan` can still read secrets; do not paste output.
- Apply order matters (network -> data -> app).
- Destroy is destructive; never run it without explicit approval.

## Docs to generate

- `docs/operations.md`: environments, plan/apply gate, rollback, ownership.
- `docs/architecture.md`: accounts, networks, data stores, trust boundaries.
- `docs/security.md`: secrets, IAM, network exposure.
