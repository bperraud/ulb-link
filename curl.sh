curl -X POST http://localhost:8080/link/api/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsImV4cCI6IjExMzIwMCJ9.ypBPljaoshBnkL_3jjHtFmvaGMsTh4Qlvie13VqtAJs"\
  -d '{"email" : "benjamin.perraudin@ulb.be", "target_url": "https://example.com/dashboard"}'
