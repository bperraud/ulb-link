curl -X PUT http://localhost:80/link/api/1 \
  -H "Content-Type: application/json" \
  -d '{"email" : "benjamin.perraudin@ulb.be", "token": "dashboard", "target_url": "https://example.com/dashboard"}'
