from app.ai_job_evaluation import meets_experience_requirement


def test_experience_filter():
    test_cases = [
        ("Minimum of 2 years of experience", True),
        ("At least 3 years of experience", True),
        ("Minimum of 5 years of experience", False),
        ("7+ years of software engineering experience", False),
        ("Junior Software Engineer - Python and SQL", True),
        ("Experience with Python and Docker preferred", True),
        ("Requires 4 years of professional experience", False),
        (
            "Minimum 2 years of experience required. "
            "5 years of experience preferred.",
            True
        ),
        (
            "2-5 years of professional experience required",
            False
        ),
        (
            "4-6 years of professional experience required",
            False
        ),
        ("3 years of professional experience", True),
        ("3+ years of professional experience", False),
        ("2+ years of professional experience", True),
        ("1-3 years of professional experience", True),
        ("2-5 years of professional experience", False)
    ]

    for description, expected in test_cases:
        result = meets_experience_requirement(description)

        assert result == expected, (
            f"Failed: {description}\n"
            f"Expected: {expected}, Got: {result}"
        )

    print("All experience filter tests passed!")


if __name__ == "__main__":
    test_experience_filter()