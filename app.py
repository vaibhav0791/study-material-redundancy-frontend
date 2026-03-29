import streamlit as st
import requests
import os
from api_client import APIClient
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Study Material Redundancy Analyzer",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #1f77b4;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration
BACKEND_URL = "http://localhost:8000"
api_client = APIClient(BACKEND_URL)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'file_ids' not in st.session_state:
    st.session_state.file_ids = []
if 'file_names' not in st.session_state:
    st.session_state.file_names = []

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    if st.button("🔗 Test Connection", use_container_width=True):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend is running!")
            else:
                st.error("❌ Backend error")
        except:
            st.error("❌ Cannot connect to backend")
    
    st.write("---")
    st.info("**Backend URL:**\nhttp://localhost:8000")

# Header
st.title("📚 Study Material Redundancy Analyzer")

st.markdown("""
An AI-powered system to analyze and reduce redundancy in your study materials.
""")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Dashboard",
    "📊 Analysis Results",
    "📈 Visualizations",
    "💾 Download Center"
])

# ============================================
# TAB 1: DASHBOARD (Upload PDFs)
# ============================================
with tab1:
    st.subheader("📤 Upload Study PDFs")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 Select one or more PDF files to analyze")
        uploaded_files = st.file_uploader(
            "Select PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
    
    with col2:
        st.write("")
        st.write("")
        analyze_button = st.button("🚀 Analyze Files", use_container_width=True, key="analyze_btn")
    
    # Show uploaded files
    if uploaded_files:
        st.write(f"✅ **You selected {len(uploaded_files)} file(s)**")
        
        for idx, file in enumerate(uploaded_files, 1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {file.name}")
            with col2:
                st.caption(f"{file.size / 1024 / 1024:.2f} MB")
        
        # When user clicks Analyze
        if analyze_button:
            st.write("---")
            progress_container = st.container()
            
            with progress_container:
                st.subheader("⏳ Processing...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Upload
                status_text.text("📤 Uploading PDFs to backend...")
                progress_bar.progress(20)
                
                upload_response = api_client.upload_pdfs(uploaded_files)
                
                if "error" in upload_response:
                    st.error(f"❌ Upload failed: {upload_response['error']}")
                else:
                    st.session_state.file_ids = [u['file_id'] for u in upload_response.get('uploads', [])]
                    st.session_state.file_names = [u['filename'] for u in upload_response.get('uploads', [])]
                    
                    status_text.text("📄 Extracting text...")
                    progress_bar.progress(40)
                    
                    for file_id in st.session_state.file_ids:
                        api_client.extract_text(file_id)
                    
                    status_text.text("🧹 Cleaning text...")
                    progress_bar.progress(60)
                    
                    for file_id in st.session_state.file_ids:
                        api_client.clean_text(file_id)
                    
                    status_text.text("🔍 Calculating similarity...")
                    progress_bar.progress(80)
                    
                    similarity_result = api_client.calculate_similarity(st.session_state.file_ids)
                    
                    if "error" not in similarity_result:
                        st.session_state.analysis_results = similarity_result
                        progress_bar.progress(100)
                        st.success("🎉 Analysis complete!")
                    else:
                        st.error("❌ Similarity calculation failed")
    else:
        st.info("No files selected yet. Upload PDFs to begin analysis.")

# ============================================
# TAB 2: ANALYSIS RESULTS
# ============================================
with tab2:
    st.subheader("📊 Analysis Results")
    
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        # Calculate metrics
        if 'statistics' in results:
            stats = results['statistics']
            mean_sim = stats.get('mean_similarity', 0)
            max_sim = stats.get('max_similarity', 0)
            min_sim = stats.get('min_similarity', 0)
        else:
            mean_sim = max_sim = min_sim = 0
        
        # Calculate most unique PDF
        file_ids = st.session_state.file_ids
        similarity_matrix = results.get('matrix', [])
        
        most_unique_idx = 0
        if len(similarity_matrix) > 0 and len(file_ids) > 0:
            # Find PDF with lowest average similarity to others
            uniqueness_scores = []
            for i in range(len(file_ids)):
                # Get average similarity to all other files
                sims = [similarity_matrix[i][j] for j in range(len(file_ids)) if i != j]
                avg_sim = sum(sims) / len(sims) if sims else 0
                uniqueness = 1 - avg_sim  # Higher is more unique
                uniqueness_scores.append(uniqueness)
            
            most_unique_idx = uniqueness_scores.index(max(uniqueness_scores))
        
        most_unique_pdf = st.session_state.file_names[most_unique_idx] if most_unique_idx < len(st.session_state.file_names) else "N/A"
        
        # Display metrics
        st.write("### Key Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📊 Total PDFs Analyzed",
                len(st.session_state.file_names),
                delta="files"
            )
        
        with col2:
            st.metric(
                "📈 Average Redundancy",
                f"{mean_sim:.2f}",
                delta="0 = unique, 1 = identical"
            )
        
        with col3:
            st.metric(
                "⭐ Most Unique PDF",
                most_unique_pdf.split('.')[0] if most_unique_pdf != "N/A" else "N/A",
                delta="lowest redundancy"
            )
        
        st.write("---")
        
        # Similarity Scores Table
        st.write("### Similarity Scores Between Documents")
        
        if similarity_matrix:
            # Create a nice dataframe for the similarity matrix
            df_similarity = pd.DataFrame(
                similarity_matrix,
                columns=[f.split('.')[0] for f in st.session_state.file_names],
                index=[f.split('.')[0] for f in st.session_state.file_names]
            )
            
            # Style the dataframe
            st.dataframe(
                df_similarity.style.format("{:.3f}").background_gradient(cmap='RdYlGn_r'),
                use_container_width=True
            )
        
        st.write("---")
        
        # Uploaded Files List
        st.write("### Uploaded Files")
        for idx, fname in enumerate(st.session_state.file_names, 1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{idx}. {fname}**")
            with col2:
                if fname == most_unique_pdf:
                    st.success("⭐ Most Unique")
    
    else:
        st.info("📊 Upload and analyze PDFs to see results here")

# ============================================
# TAB 3: VISUALIZATIONS
# ============================================
with tab3:
    st.subheader("📈 Visualization Dashboard")
    
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        similarity_matrix = results.get('matrix', [])
        file_names = [f.split('.')[0] for f in st.session_state.file_names]
        
        # 1. REDUNDANCY HEATMAP
        st.write("### 🔥 Redundancy Heatmap")
        
        if similarity_matrix:
            # Create heatmap
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=similarity_matrix,
                x=file_names,
                y=file_names,
                colorscale='RdYlGn_r',
                text=np.array(similarity_matrix).round(3),
                texttemplate='%{text:.3f}',
                textfont={"size": 12},
                colorbar=dict(title="Similarity")
            ))
            
            fig_heatmap.update_layout(
                title="Document Similarity Heatmap",
                xaxis_title="Documents",
                yaxis_title="Documents",
                height=500,
                width=800
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # 2. SIMILARITY DISTRIBUTION
        st.write("### 📊 Similarity Distribution")
        
        if similarity_matrix:
            # Extract upper triangle (avoid duplicates)
            similarity_scores = []
            labels = []
            for i in range(len(similarity_matrix)):
                for j in range(i+1, len(similarity_matrix)):
                    sim = similarity_matrix[i][j]
                    similarity_scores.append(sim)
                    labels.append(f"{file_names[i]} vs {file_names[j]}")
            
            # Create bar chart
            df_dist = pd.DataFrame({
                'Document Pair': labels,
                'Similarity Score': similarity_scores
            })
            
            fig_bar = px.bar(
                df_dist,
                x='Document Pair',
                y='Similarity Score',
                color='Similarity Score',
                color_continuous_scale='RdYlGn_r',
                title="Similarity Scores Between Documents",
                labels={'Similarity Score': 'Similarity (0-1)'}
            )
            
            fig_bar.update_layout(
                height=400,
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # 3. CLUSTERING VISUALIZATION
        st.write("### 🎯 Clustering Information")
        
        stats = results.get('statistics', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Mean Similarity",
                f"{stats.get('mean_similarity', 0):.3f}",
                delta="average redundancy"
            )
        
        with col2:
            st.metric(
                "Max Similarity",
                f"{stats.get('max_similarity', 0):.3f}",
                delta="highest redundancy"
            )
        
        with col3:
            st.metric(
                "Min Similarity",
                f"{stats.get('min_similarity', 0):.3f}",
                delta="lowest redundancy"
            )
        
        st.info("📌 Documents with high similarity (0.7+) have significant overlapping content and may be consolidated.")
    
    else:
        st.info("📈 Upload and analyze PDFs to see visualizations here")

# ============================================
# TAB 4: DOWNLOAD CENTER
# ============================================
with tab4:
    st.subheader("💾 Download Center")
    
    st.info("Download your analysis results and clean study materials")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📥 Original PDFs")
        
        if st.session_state.file_names:
            st.success(f"✅ {len(st.session_state.file_names)} file(s) available")
            
            for fname in st.session_state.file_names:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"📄 {fname}")
                with col_b:
                    if st.button("📥", key=f"download_{fname}"):
                        st.info(f"Download link for {fname} would be generated here")
        else:
            st.info("No files uploaded yet")
    
    with col2:
        st.write("### ✨ Clean Study Material")
        
        if st.session_state.analysis_results and st.session_state.file_ids:
            st.success("✅ Clean material is ready!")
            
            # Create a container for the download
            download_placeholder = st.empty()
            
            # Button to trigger generation
            if st.button("📥 Generate & Download Clean PDF", key="generate_clean", use_container_width=True):
                with st.spinner("⏳ Generating clean material..."):
                    # Call backend to generate clean PDF
                    clean_result = api_client.generate_clean_pdf(st.session_state.file_ids)
                    
                    if "error" not in clean_result:
                        # Show info about the file
                        st.write("""
                        **File Details:**
                        - **Filename:** clean_study_material.txt
                        - **Content:** Deduplicated content from all PDFs
                        
                        **This file contains:**
                        - ✅ Deduplicated content from all PDFs
                        - ✅ Removed redundant sections
                        - ✅ Combined unique information
                        - ✅ Ready for study
                        """)
                        
                        # Download button with actual content
                        st.download_button(
                            label="⬇️ Click Here to Download File",
                            data=clean_result.get('content', ''),
                            file_name="clean_study_material.txt",
                            mime="text/plain",
                            key="actual_download_button"
                        )
                        
                        st.success("✅ File is ready! Click the download button above!")
                    else:
                        st.error(f"❌ Failed to generate: {clean_result.get('error')}")
        else:
            st.info("📊 Analyze PDFs first to generate clean material")
    
    st.write("---")
    
    st.write("### 📊 Export Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.analysis_results:
            # Create CSV from similarity matrix
            df = pd.DataFrame(
                st.session_state.analysis_results.get('matrix', []),
                columns=st.session_state.file_names,
                index=st.session_state.file_names
            )
            csv = df.to_csv()
            st.download_button(
                label="📊 Export as CSV",
                data=csv,
                file_name="similarity_results.csv",
                mime="text/csv",
                key="csv_download",
                use_container_width=True
            )
        else:
            st.info("No analysis results to export")
    
    with col2:
        if st.session_state.analysis_results:
            import json
            json_str = json.dumps(st.session_state.analysis_results, indent=2)
            st.download_button(
                label="📋 Export as JSON",
                data=json_str,
                file_name="similarity_results.json",
                mime="application/json",
                key="json_download",
                use_container_width=True
            )
        else:
            st.info("No analysis results to export")
    
    with col3:
        if st.session_state.analysis_results:
            report = f"""STUDY MATERIAL REDUNDANCY ANALYSIS REPORT
==========================================

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
-------
Total PDFs Analyzed: {len(st.session_state.file_names)}

Files Analyzed:
{chr(10).join([f"- {fname}" for fname in st.session_state.file_names])}

SIMILARITY STATISTICS
---------------------
Mean Similarity: {st.session_state.analysis_results.get('statistics', {}).get('mean_similarity', 0):.3f}
Max Similarity: {st.session_state.analysis_results.get('statistics', {}).get('max_similarity', 0):.3f}
Min Similarity: {st.session_state.analysis_results.get('statistics', {}).get('min_similarity', 0):.3f}

INTERPRETATION
---------------
- Mean Similarity 0.69 = 69% average overlap (Moderate redundancy)
- Files with >0.7 similarity have significant overlap and can be consolidated
- Files with <0.3 similarity have unique content worth keeping

RECOMMENDATION
---------------
1. Consolidate files with similarity > 0.7
2. Keep files with similarity < 0.3 as they have unique content
3. Use the "Clean Study Material" download to get deduplicated version
4. Review the Redundancy Heatmap to identify specific overlaps

NEXT STEPS
----------
1. Download the Clean Study Material PDF
2. Review it for quality
3. Use it as your main study guide
4. Keep original files as backup reference

==========================================
Study Material Redundancy Analyzer v1.0
                """
            st.download_button(
                label="📄 Export as Report",
                data=report,
                file_name="analysis_report.txt",
                mime="text/plain",
                key="report_download",
                use_container_width=True
            )
        else:
            st.info("No analysis results to export")

# Footer
st.write("---")
st.caption("📚 Study Material Redundancy Analyzer | v1.0 | Built with ❤️ for Data Science")