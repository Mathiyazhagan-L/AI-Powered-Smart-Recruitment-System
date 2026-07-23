# End-to-End Test Report

## Test Execution Summary
- **Date**: 2026-06-24 18:09:14
- **Status**: PASSED
- **Total Duration**: 4.2s

## Test Steps
1. **Candidate Registration**: SUCCESS
2. **Profile Completion**: SUCCESS
3. **Resume Upload**: SUCCESS
4. **Assessment Completion**: SUCCESS
5. **Job Publish**: SUCCESS
6. **Candidate Application**: SUCCESS
7. **ATS Score Generated**: SUCCESS
8. **HR Review Transition**: SUCCESS
9. **Interview Scheduled**: SUCCESS
10. **Interview Completed**: SUCCESS
11. **Offer Generated**: SUCCESS
12. **Offer Accepted**: SUCCESS
13. **Final Status**: Hired

## Verification
- Database Application state transitioned through: `Applied -> Screening -> Assessment -> Interview -> Selected -> Hired`
- Email Triggers fired: 5
- Data persistence verified across all microservices.
