"""
Streamlit demo UI for Smart Shortlisting Engine.
"""

import streamlit as st
import os
import json
from pipeline import ShortlistingPipeline


def main():
    st.set_page_config(
        page_title="Smart Shortlisting Engine",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Smart Shortlisting Engine")
    st.markdown("""
    Rank candidates for a job posting using deterministic matching algorithms 
    (keyword/skill matching and semantic similarity), not LLM judgment.
    """)
    
    st.sidebar.header("Configuration")
    
    # File upload
    st.sidebar.subheader("Upload Documents")
    jd_file = st.sidebar.file_uploader(
        "Job Description (PDF)",
        type="pdf",
        key="jd_upload"
    )
    
    resume_files = st.sidebar.file_uploader(
        "Resumes (PDFs - multiple allowed)",
        type="pdf",
        accept_multiple_files=True,
        key="resume_upload"
    )
    
    # Weights configuration
    st.sidebar.subheader("Score Weights")
    keyword_weight = st.sidebar.slider(
        "Keyword Match Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1
    )
    semantic_weight = 1.0 - keyword_weight
    
    st.sidebar.markdown(f"""
    **Weights:**
    - Keyword: {keyword_weight:.1f}
    - Semantic: {semantic_weight:.1f}
    """)
    
    # Process button
    process_button = st.sidebar.button("🚀 Run Shortlisting", type="primary")
    
    # Main content area
    if process_button:
        if not jd_file:
            st.error("Please upload a Job Description PDF")
            return
        
        if not resume_files:
            st.error("Please upload at least one resume PDF")
            return
        
        # Save uploaded files temporarily
        with st.spinner("Processing documents..."):
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save JD
            jd_path = os.path.join(temp_dir, "jd.pdf")
            with open(jd_path, "wb") as f:
                f.write(jd_file.getbuffer())
            
            # Save resumes
            resume_folder = os.path.join(temp_dir, "resumes")
            os.makedirs(resume_folder, exist_ok=True)
            
            for resume_file in resume_files:
                resume_path = os.path.join(resume_folder, resume_file.name)
                with open(resume_path, "wb") as f:
                    f.write(resume_file.getbuffer())
            
            # Run pipeline
            try:
                pipeline = ShortlistingPipeline()
                
                # Update weights
                from config import KEYWORD_WEIGHT, SEMANTIC_WEIGHT
                import config
                config.KEYWORD_WEIGHT = keyword_weight
                config.SEMANTIC_WEIGHT = semantic_weight
                
                output_path = os.path.join(temp_dir, "output.json")
                output = pipeline.run(jd_path, resume_folder, output_path)
                
                # Display results
                display_results(output)
                
                # Download button
                st.download_button(
                    label="📥 Download Results (JSON)",
                    data=json.dumps(output, indent=2),
                    file_name="shortlisting_results.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                st.exception(e)
    
    else:
        # Show instructions when not processing
        st.info("👆 Upload a JD and resumes in the sidebar, then click 'Run Shortlisting'")
        
        st.markdown("""
        ## How It Works
        
        ### 1. Keyword/Skill Matching
        - Normalizes skill names (e.g., "ReactJS" → "React")
        - Uses fuzzy matching for typos (85% similarity threshold)
        - Required skills: 2 points, Nice-to-have: 1 point
        
        ### 2. Semantic Matching
        - Uses sentence-transformers embeddings
        - Computes cosine similarity between JD and resume chunks
        - Aggregates using top-3 mean similarity
        
        ### 3. Score Fusion
        - Formula: `final_score = w₁ × keyword + w₂ × semantic`
        - Default weights: 50/50 (adjustable in sidebar)
        - Min-max normalization for meaningful spread
        
        ### 4. Output
        - Ranked list of all candidates
        - Detailed explanations for top 3
        - Traceable skill matching with evidence
        """)


def display_results(output):
    """Display the shortlisting results."""
    # JD Summary
    st.header("📋 Job Description Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Role", output['jd_summary']['role_title'])
    col2.metric("Experience Level", output['jd_summary']['experience_level'])
    col3.metric("Total Candidates", output['metadata']['total_candidates'])
    
    st.subheader("Required Skills")
    st.write(", ".join(output['jd_summary']['required_skills']))
    
    if output['jd_summary']['nice_to_have_skills']:
        st.subheader("Nice-to-Have Skills")
        st.write(", ".join(output['jd_summary']['nice_to_have_skills']))
    
    # Rankings
    st.header("🏆 Candidate Rankings")
    
    # Create dataframe for display
    import pandas as pd
    df = pd.DataFrame(output['rankings'])
    
    # Display as interactive table
    st.dataframe(
        df[['rank', 'name', 'final_score', 'keyword_score', 'semantic_score', 'years_of_experience']],
        column_config={
            'rank': st.column_config.NumberColumn('Rank', width='small'),
            'name': st.column_config.TextColumn('Candidate Name', width='medium'),
            'final_score': st.column_config.NumberColumn('Final Score', format='%.1f'),
            'keyword_score': st.column_config.NumberColumn('Keyword', format='%.1f'),
            'semantic_score': st.column_config.NumberColumn('Semantic', format='%.1f'),
            'years_of_experience': st.column_config.NumberColumn('Years Exp', format='%d')
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Score distribution chart
    st.subheader("Score Distribution")
    import plotly.express as px
    
    fig = px.scatter(
        df,
        x='keyword_score',
        y='semantic_score',
        size='final_score',
        hover_name='name',
        title='Keyword vs Semantic Scores',
        labels={
            'keyword_score': 'Keyword Score',
            'semantic_score': 'Semantic Score',
            'final_score': 'Final Score'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 3 Explanations
    st.header("🎯 Top 3 Candidates - Detailed Analysis")
    
    for i, expl in enumerate(output['top_3_explanations'], 1):
        with st.expander(f"#{i} - {expl['name']} (Score: {expl['final_score']:.1f})", expanded=(i == 1)):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("✅ Matched Skills")
                for skill in expl['matched_skills']:
                    st.success(f"• {skill}")
                
                if expl['missing_skills']:
                    st.subheader("❌ Missing Skills")
                    for skill in expl['missing_skills']:
                        st.error(f"• {skill}")
            
            with col2:
                st.subheader("📊 Match Statistics")
                st.metric(
                    "Required Skills Matched",
                    f"{expl['required_match_count']}/{expl['total_required']}"
                )
                
                st.subheader("💡 Summary")
                st.write(expl['summary'])
                
                if expl.get('skill_evidence'):
                    st.subheader("📝 Skill Evidence")
                    for skill, evidence in expl['skill_evidence'].items():
                        with st.echo():
                            st.write(f"**{skill}**: ...{evidence}...")


if __name__ == "__main__":
    main()
