# Smart Shortlisting Engine

A system that ranks candidates for a job posting using deterministic matching algorithms (keyword/skill matching and semantic similarity), not LLM judgment.

## Matching Approach

### 1. Keyword/Skill Matching
- **Skill Normalization**: Uses an alias dictionary to map synonyms (e.g., "ReactJS" → "React", "Node" → "Node.js")
- **Fuzzy Matching**: Uses `rapidfuzz` to handle typos and near-matches (threshold: 85% similarity)
- **Scoring**: 
  - Required skills: 2 points each
  - Nice-to-have skills: 1 point each
  - Score normalized to 0-100 scale

### 2. Semantic Matching
- **Embeddings**: Uses `sentence-transformers` (all-MiniLM-L6-v2) to create vector embeddings
- **Chunking**: JD responsibilities and resume project descriptions are chunked into sentences
- **Similarity**: Computes cosine similarity between JD chunks and resume chunks
- **Aggregation**: Uses top-3 mean similarity to capture conceptual relevance
- **Score**: Normalized to 0-100 scale

### 3. Score Fusion
- **Formula**: `final_score = 0.5 * keyword_score + 0.5 * semantic_score`
- **Rationale**: Equal weighting ensures both explicit skill matching and conceptual fit contribute equally
- **Normalization**: Both sub-scores normalized to 0-100 before fusion

## Pipeline Stages

1. **Data Ingestion**: Parse PDFs, extract structured information
2. **Keyword Matching**: Explicit skill/tool matching with normalization
3. **Semantic Matching**: Conceptual similarity using embeddings
4. **Score Fusion**: Combine sub-scores with documented weights
5. **Ranking**: Sort candidates by final score
6. **Explanation**: Generate traceable explanations for top 3

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up MongoDB credentials:
```bash
cp .env.example .env
# Edit .env with your MongoDB credentials
```

3. Configure MongoDB connection in `.env`:
```
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_CLUSTER=your_cluster.mongodb.net
MONGODB_DATABASE=smart_shortlisting
```

## Usage

### CLI
```bash
python main.py --jd path/to/jd.pdf --resumes path/to/resumes_folder
```

### Streamlit UI
```bash
streamlit run app.py
```

### API
```bash
uvicorn api:app --reload
```

## Vercel Deployment

Deploy the Smart Shortlisting Engine to Vercel as a serverless API.

### Prerequisites

1. Install Vercel CLI:
```bash
npm install -g vercel
```

 or use the Vercel dashboard.

2. Set up environment variables in Vercel:
   - Go to your Vercel project settings
   - Add the following environment variables:
     - `MONGODB_USERNAME`: Your MongoDB username
     - `MONGODB_PASSWORD`: Your MongoDB password
     - `MONGODB_CLUSTER`: Your MongoDB cluster (e.g., `cluster0.aofhzxk.mongodb.net`)
     - `MONGODB_DATABASE`: Database name (e.g., `smart_shortlisting`)

### Deployment Steps

1. Push your code to GitHub

2. Deploy via Vercel CLI:
```bash
cd smart_shortlisting
vercel
```

3. Follow the prompts to configure your project

4. Or deploy via Vercel dashboard:
   - Import your GitHub repository
   - Vercel will automatically detect the Python project
   - Configure environment variables
   - Click Deploy

### API Endpoints

Once deployed, your API will be available at:

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /shortlist` - Run shortlisting pipeline

### Using the Deployed API

```bash
# Upload JD and resumes
curl -X POST https://your-project.vercel.app/shortlist \
  -F "jd=@jd.pdf" \
  -F "resumes=@resumes.zip" \
  -F "keyword_weight=0.5" \
  -F "semantic_weight=0.5"
```

Or use a single PDF for resumes:
```bash
curl -X POST https://your-project.vercel.app/shortlist \
  -F "jd=@jd.pdf" \
  -F "resumes=@resume.pdf"
```

## MongoDB Integration

The system automatically saves shortlisting results to MongoDB when configured. Results are stored in the `shortlistings` collection with the following structure:

- JD information (role, skills, experience level)
- Complete candidate rankings
- Top 3 explanations
- Timestamp and metadata

To disable MongoDB, set `use_mongodb=False` when initializing the pipeline:
```python
pipeline = ShortlistingPipeline(use_mongodb=False)
```

## Database Operations

The `database.py` module provides CRUD operations:

```python
from database import MongoDB

db = MongoDB()

# Save a result
db.save_shortlisting_result(jd_path, output, resume_count)

# Retrieve by ID
result = db.get_shortlisting_by_id(shortlisting_id)

# Get all results
all_results = db.get_all_shortlistings(limit=10)

# Search by role
results = db.get_shortlistings_by_role("Python Developer")

# Delete a result
db.delete_shortlisting(shortlisting_id)
```

## Output Format

```json
{
  "jd_summary": {
    "role_title": "...",
    "required_skills": [...],
    "nice_to_have_skills": [...],
    "responsibilities": [...],
    "experience_level": "..."
  },
  "rankings": [
    {
      "rank": 1,
      "name": "...",
      "final_score": 92.3,
      "keyword_score": 88,
      "semantic_score": 95
    }
  ],
  "top_3_explanations": [
    {
      "name": "...",
      "matched_skills": ["Python", "React"],
      "missing_skills": ["AWS"],
      "summary": "..."
    }
  ]
}
```
