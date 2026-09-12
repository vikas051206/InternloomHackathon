# Sample Data Structure

This folder contains sample data for testing the Smart Shortlisting Engine.

## Structure

```
sample_data/
├── jd/                    # Job Description PDFs
│   └── sample_jd.pdf     # Sample job description
└── resumes/              # Resume PDFs
    ├── resume_1.pdf
    ├── resume_2.pdf
    └── ...
```

## Usage

Place your JD PDF in the `jd/` folder and resume PDFs in the `resumes/` folder.

Then run:
```bash
python main.py --jd sample_data/jd/sample_jd.pdf --resumes sample_data/resumes
```

Or use the Streamlit UI and upload the files directly.
