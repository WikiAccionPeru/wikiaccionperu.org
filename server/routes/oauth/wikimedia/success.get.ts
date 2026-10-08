// Alias: the Lingua Libre consumer has this fixed callback path (http://localhost:8079/oauth/wikimedia/success).
export default defineEventHandler((event) => handleOAuthCallback(event))
