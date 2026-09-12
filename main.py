"""
CLI entry point for Smart Shortlisting Engine.
"""

import argparse
import os
from pipeline import ShortlistingPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Smart Shortlisting Engine - Rank candidates using deterministic matching"
    )
    parser.add_argument(
        "--jd",
        required=True,
        help="Path to Job Description PDF"
    )
    parser.add_argument(
        "--resumes",
        required=True,
        help="Path to folder containing resume PDFs"
    )
    parser.add_argument(
        "--output",
        default="output.json",
        help="Path to save output JSON (default: output.json)"
    )
    parser.add_argument(
        "--keyword-weight",
        type=float,
        default=0.5,
        help="Weight for keyword matching score (default: 0.5)"
    )
    parser.add_argument(
        "--semantic-weight",
        type=float,
        default=0.5,
        help="Weight for semantic matching score (default: 0.5)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.jd):
        print(f"Error: JD file not found: {args.jd}")
        return
    
    if not os.path.exists(args.resumes):
        print(f"Error: Resume folder not found: {args.resumes}")
        return
    
    # Update weights if provided
    if args.keyword_weight or args.semantic_weight:
        import config
        config.KEYWORD_WEIGHT = args.keyword_weight
        config.SEMANTIC_WEIGHT = args.semantic_weight
        print(f"Using custom weights: keyword={args.keyword_weight}, semantic={args.semantic_weight}")
    
    # Run pipeline
    try:
        pipeline = ShortlistingPipeline()
        output = pipeline.run(args.jd, args.resumes, args.output)
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📁 Output saved to: {args.output}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
