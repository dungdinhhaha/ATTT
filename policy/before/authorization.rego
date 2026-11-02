package minibank.authz

# INSECURE DEMO POLICY: authenticated subjects are allowed without checking
# action, resource ownership, support ticket, role, MFA, or business limits.
default allow := false

allow if {
    input.subject != ""
}
