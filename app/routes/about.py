from fastapi import APIRouter

router = APIRouter(tags=["about"])


@router.get("/about")
def about():
    return {
        "name": "Shivam Chauhan",
        "email": "22bme054@iiitdmj.ac.in",
        "my features": {
            "Google OAuth 2.0": "Integrated professional social login to provide a seamless and secure user experience.",
            "SMTP Email OTP": "Implemented multi-factor authentication via real email verification for enhanced account security.",
            "Premium Glassmorphism UI": "Designed a modern, responsive frontend to demonstrate high-end product sense and aesthetic standards.",
            "Note Version History": "Every note update stores previous versions for tracking changes.",
            "Pin Notes": "Allows users to pin important notes for quick access."
        },
    }
