package minibank.authz

default allow := false

# Customer may read only an account owned by the authenticated subject.
allow if {
    input.action == "account_read"
    input.subject == input.owner
}

# Support may read an account only when a server-verified ticket exists.
allow if {
    input.action == "support_read"
    input.role == "support"
    input.ticket == true
}

allow if {
    input.action == "admin_list"
    input.role == "admin"
}

# Admin role changes require MFA and prohibit self-change.
allow if {
    input.action == "admin_role_write"
    input.role == "admin"
    input.mfa == true
    input.subject != input.target
}

allow if {
    input.action == "profile_write"
    input.subject == input.target
}

allow if {
    input.action == "transfer_create"
    input.subject == input.owner
}
