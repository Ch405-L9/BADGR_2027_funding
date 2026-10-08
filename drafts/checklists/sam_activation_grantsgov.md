# DRAFT — SAM activation and Grants.gov checklist
Status: DRAFT checklist. Checked: 2026-10-08 (America/New_York). Tick items only with evidence; nothing here submits anything.

While SAM is pending (submitted 2026-09-29):
- [ ] Watch for SAM emails; answer validation requests only inside SAM.gov
- [ ] APEX review of LLC vs. sole-prop classification (D4)
- [ ] Decide with APEX whether to update SAM receipts ($815) to match the 2025 return ($5,550) (D3)
On activation:
- [ ] Record CAGE code, activation date and expiration date in context/business_profile.json
- [ ] Set a renewal reminder before expiration
- [ ] Grants.gov: register, link the UEI, assign the E-Business Point of Contact and roles
- [ ] SBIR.gov company registry; Research.gov account (verify current NSF requirements)
- [ ] Re-run `python3 -m badgr_funding.cli rank -v`; SAM-gated rows unblock

## Missing inputs
- Every unticked item above.
