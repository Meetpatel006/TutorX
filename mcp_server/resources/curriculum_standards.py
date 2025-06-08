"""
Curriculum standards for different countries and education systems.
"""
from typing import Dict, Any

# Sample curriculum standards data
CURRICULUM_STANDARDS = {
    "us": {
        "name": "Common Core State Standards (US)",
        "subjects": {
            "math": {
                "k-5": ["Counting & Cardinality", "Operations & Algebraic Thinking", "Number & Operations"],
                "6-8": ["Ratios & Proportional Relationships", "The Number System", "Expressions & Equations"],
                "9-12": ["Number & Quantity", "Algebra", "Functions", "Modeling", "Geometry", "Statistics & Probability"]
            },
            "ela": {
                "k-5": ["Reading: Literature", "Reading: Informational Text", "Foundational Skills"],
                "6-12": ["Reading: Literature", "Reading: Informational Text", "Writing", "Speaking & Listening", "Language"]
            },
            "csta": {
                "k-5": ["Algorithms & Programming", "Computing Systems", "Data & Analysis", "Impacts of Computing"],
                "6-8": ["Algorithms & Programming", "Computing Systems", "Data & Analysis", "Impacts of Computing", "Networks & Internet"],
                "9-12": ["Algorithms & Programming", "Computing Systems", "Data & Analysis", "Impacts of Computing", "Networks & Internet"]
            }
        },
        "url": "http://www.corestandards.org/"
    },
    "uk": {
        "name": "National Curriculum (UK)",
        "subjects": {
            "computing": {
                "ks1": ["Computer Science", "Information Technology", "Digital Literacy"],
                "ks2": ["Computer Science", "Information Technology", "Digital Literacy"],
                "ks3": ["Computer Science", "Information Technology", "Digital Literacy"],
                "ks4": ["Computer Science", "Information Technology", "Creative iMedia"]
            },
            "maths": {
                "ks1": ["Number", "Measurement", "Geometry", "Statistics"],
                "ks2": ["Number", "Ratio & Proportion", "Algebra", "Measurement", "Geometry", "Statistics"]
            }
        },
        "url": "https://www.gov.uk/government/collections/national-curriculum"
    },
    "in": {
        "name": "National Education Policy (India)",
        "subjects": {
            "mathematics": {
                "foundation": ["Numeracy", "Shapes & Spatial Understanding"],
                "preparatory": ["Numbers", "Basic Mathematical Operations", "Shapes & Geometry"],
                "middle": ["Number System", "Algebra", "Geometry", "Mensuration", "Data Handling"],
                "secondary": ["Number Systems", "Algebra", "Coordinate Geometry", "Geometry", "Trigonometry", "Mensuration", "Statistics & Probability"]
            },
            "computer_science": {
                "middle": ["Computational Thinking", "Computer Systems", "Networking", "Data Analysis"],
                "secondary": ["Programming", "Computer Networks", "Database Management", "Web Technologies"]
            }
        },
        "url": "https://www.education.gov.in/en/nep2020"
    },
    "sg": {
        "name": "Singapore Curriculum",
        "subjects": {
            "mathematics": {
                "primary": ["Number & Algebra", "Measurement & Geometry", "Statistics"],
                "secondary": ["Number & Algebra", "Geometry & Measurement", "Statistics & Probability", "Trigonometry & Calculus"]
            },
            "computing": {
                "primary": ["Computational Thinking", "Coding", "Digital Literacy"],
                "secondary": ["Computing", "Infocomm", "Media Studies"]
            }
        },
        "url": "https://www.moe.gov.sg/"
    },
    "ca": {
        "name": "Canadian Curriculum",
        "subjects": {
            "mathematics": {
                "elementary": ["Number Sense & Numeration", "Measurement", "Geometry & Spatial Sense", "Patterning & Algebra", "Data Management & Probability"],
                "secondary": ["Mathematics", "Advanced Functions", "Calculus & Vectors", "Data Management"]
            },
            "computer_studies": {
                "grades_10-12": ["Computer Science", "Computer Engineering", "Computer Programming"]
            }
        },
        "url": "https://www.cmec.ca/"
    }
}

def get_curriculum_standards(country_code: str = "us") -> Dict[str, Any]:
    """
    Get curriculum standards for a specific country.
    
    Args:
        country_code: ISO country code (e.g., 'us', 'uk', 'in', 'sg', 'ca')
        
    Returns:
        Dictionary containing curriculum standards for the specified country
    """
    country_code = country_code.lower()
    if country_code not in CURRICULUM_STANDARDS:
        return {
            "error": f"Curriculum standards for country code '{country_code}' not found. "
                    f"Available countries: {', '.join(CURRICULUM_STANDARDS.keys())}"
        }
    
    return CURRICULUM_STANDARDS[country_code]
