curl -X POST http://localhost:80/link/api/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJleHAiOjE4MTM0MzI5MTAsImVtYWlsIjoiYmVuamFtaW4ucGVycmF1ZGluQHVsYi5iZSJ9.4nQ_-NkUQ9SmzUzVhdxTai0duJkyyod4KTDCjnzj1ug"\
  -d '{"email" : "benjamin.perraudin@ulb.be", "target_url": "https://example.com/dashboard"}'
