"""
Configuration settings for the Smart Shortlisting Engine.
"""

# Score fusion weights
KEYWORD_WEIGHT = 0.5
SEMANTIC_WEIGHT = 0.5

# Fuzzy matching threshold (0-100)
FUZZY_MATCH_THRESHOLD = 85

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Semantic matching: number of top chunks to average
TOP_K_CHUNKS = 3

# Skill scoring weights
REQUIRED_SKILL_WEIGHT = 2
NICE_TO_HAVE_SKILL_WEIGHT = 1

# Section headers for resume parsing (case-insensitive)
RESUME_SECTIONS = {
    "skills": ["skills", "technical skills", "tech stack", "technologies", "tools"],
    "experience": ["experience", "work experience", "employment", "work history"],
    "projects": ["projects", "project experience", "key projects"],
    "education": ["education", "academic", "qualifications"]
}

# Skill alias dictionary for normalization
SKILL_ALIASES = {
    # JavaScript frameworks
    "reactjs": "react",
    "react.js": "react",
    "reactjs": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    
    # Backend
    "node": "node.js",
    "nodejs": "node.js",
    "express": "express.js",
    "expressjs": "express.js",
    
    # Databases
    "postgres": "postgresql",
    "mongo": "mongodb",
    "mongo db": "mongodb",
    "mysql": "mysql",
    "sqlite": "sqlite",
    
    # Cloud
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "azure": "microsoft azure",
    
    # DevOps
    "docker": "docker",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    
    # Languages
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "cpp": "c++",
    "cs": "c#",
    
    # Tools
    "gitlab": "gitlab",
    "github": "github",
    "jira": "jira",
    "confluence": "confluence",
}
