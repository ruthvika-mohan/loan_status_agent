def get_loan_status(phone):
    mock_db = {
        "9999999999": "UNDER_REVIEW",
        "8888888888": "APPROVED"
    }

    return mock_db.get(phone, "NOT_FOUND")
