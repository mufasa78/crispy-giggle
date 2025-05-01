import streamlit as st
import requests
import json
import pandas as pd
import os
from datetime import datetime
from urllib.parse import urlparse

# Set page config
st.set_page_config(
    page_title="Shopee Data API",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define API URLs
API_BASE_URL = os.environ.get("API_URL", "http://localhost:5000/api/v1")

# Helper functions
def format_datetime(dt_str):
    """Format datetime string for display"""
    if not dt_str:
        return "-"
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def extract_shopee_ids(url):
    """Extract shop_id and item_id from Shopee URL"""
    try:
        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        
        # Check if URL has the correct format
        if "-i." not in path:
            return None, None
        
        # Extract IDs
        id_part = path.split("-i.")[1]
        shop_id, item_id = id_part.split(".")
        
        return shop_id, item_id
    except:
        return None, None

def create_job(api_key, deals):
    """Create a new job with multiple deals"""
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    response = requests.post(
        f"{API_BASE_URL}/job/create",
        headers=headers,
        json={"deals": deals}
    )
    return response.json()

def get_job_results(api_key, job_id):
    """Get job results"""
    headers = {"X-API-Key": api_key}
    response = requests.get(
        f"{API_BASE_URL}/job/result/{job_id}",
        headers=headers
    )
    return response.json()

def cancel_job(api_key, job_id):
    """Cancel a job"""
    headers = {"X-API-Key": api_key}
    response = requests.post(
        f"{API_BASE_URL}/job/cancel/{job_id}",
        headers=headers
    )
    return response.json()

# Sidebar for API key input
with st.sidebar:
    st.title("🛍️ Shopee Data API")
    api_key = st.text_input("API Key", type="password")
    st.divider()
    
    # Navigation
    page = st.radio("Navigation", ["Extract Data", "Check Results", "Documentation"])
    
    st.divider()
    st.markdown("### About")
    st.markdown("This app allows you to extract product data from Shopee Taiwan using the API.")
    st.markdown("Made with ❤️ by Your Company")

# Main content
if page == "Extract Data":
    st.title("Extract Shopee Product Data")
    
    # Input method selection
    input_method = st.radio("Input Method", ["Single URL", "Multiple URLs", "CSV Upload"])
    
    if input_method == "Single URL":
        # Single URL input
        url = st.text_input("Shopee Product URL", placeholder="https://shopee.tw/product-name-i.104581011.24901963692")
        
        if url:
            shop_id, item_id = extract_shopee_ids(url)
            if not shop_id or not item_id:
                st.error("Invalid Shopee URL format. Please enter a valid URL.")
            else:
                st.success(f"Valid Shopee URL. Shop ID: {shop_id}, Item ID: {item_id}")
                
                if st.button("Extract Data"):
                    if not api_key:
                        st.error("Please enter your API key in the sidebar.")
                    else:
                        with st.spinner("Creating job..."):
                            deals = [{
                                "deal_id": f"{shop_id}.{item_id}",
                                "step_id": "1",
                                "priority": 1
                            }]
                            
                            result = create_job(api_key, deals)
                            
                            if result.get("success"):
                                job_id = result["data"]["vendor_job_id"]
                                st.success(f"Job created successfully! Job ID: {job_id}")
                                st.info("You can check the results in the 'Check Results' tab.")
                                
                                # Add job_id to session state
                                if "jobs" not in st.session_state:
                                    st.session_state.jobs = []
                                st.session_state.jobs.append(job_id)
                            else:
                                st.error(f"Error creating job: {result.get('message', 'Unknown error')}")
    
    elif input_method == "Multiple URLs":
        # Multiple URLs input
        urls = st.text_area("Shopee Product URLs (one per line)", height=200)
        
        if urls:
            url_list = [url.strip() for url in urls.split("\n") if url.strip()]
            valid_urls = []
            invalid_urls = []
            
            for url in url_list:
                shop_id, item_id = extract_shopee_ids(url)
                if shop_id and item_id:
                    valid_urls.append({
                        "url": url,
                        "shop_id": shop_id,
                        "item_id": item_id
                    })
                else:
                    invalid_urls.append(url)
            
            st.write(f"Found {len(valid_urls)} valid URLs and {len(invalid_urls)} invalid URLs.")
            
            if invalid_urls:
                with st.expander("Show invalid URLs"):
                    for url in invalid_urls:
                        st.write(url)
            
            if valid_urls:
                if st.button("Extract Data from All Valid URLs"):
                    if not api_key:
                        st.error("Please enter your API key in the sidebar.")
                    else:
                        with st.spinner("Creating job..."):
                            deals = [{
                                "deal_id": f"{url['shop_id']}.{url['item_id']}",
                                "step_id": str(i),
                                "priority": i
                            } for i, url in enumerate(valid_urls, 1)]
                            
                            result = create_job(api_key, deals)
                            
                            if result.get("success"):
                                job_id = result["data"]["vendor_job_id"]
                                st.success(f"Job created successfully! Job ID: {job_id}")
                                st.info("You can check the results in the 'Check Results' tab.")
                                
                                # Add job_id to session state
                                if "jobs" not in st.session_state:
                                    st.session_state.jobs = []
                                st.session_state.jobs.append(job_id)
                            else:
                                st.error(f"Error creating job: {result.get('message', 'Unknown error')}")
    
    elif input_method == "CSV Upload":
        # CSV upload
        st.info("Upload a CSV file with Shopee product URLs in the first column.")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                if len(df.columns) == 0:
                    st.error("The CSV file is empty.")
                else:
                    # Extract URLs from the first column
                    urls = df.iloc[:, 0].tolist()
                    valid_urls = []
                    invalid_urls = []
                    
                    for url in urls:
                        if isinstance(url, str):
                            shop_id, item_id = extract_shopee_ids(url)
                            if shop_id and item_id:
                                valid_urls.append({
                                    "url": url,
                                    "shop_id": shop_id,
                                    "item_id": item_id
                                })
                            else:
                                invalid_urls.append(url)
                    
                    st.write(f"Found {len(valid_urls)} valid URLs and {len(invalid_urls)} invalid URLs.")
                    
                    if invalid_urls:
                        with st.expander("Show invalid URLs"):
                            for url in invalid_urls:
                                st.write(url)
                    
                    if valid_urls:
                        if st.button("Extract Data from All Valid URLs"):
                            if not api_key:
                                st.error("Please enter your API key in the sidebar.")
                            else:
                                with st.spinner("Creating job..."):
                                    deals = [{
                                        "deal_id": f"{url['shop_id']}.{url['item_id']}",
                                        "step_id": str(i),
                                        "priority": i
                                    } for i, url in enumerate(valid_urls, 1)]
                                    
                                    result = create_job(api_key, deals)
                                    
                                    if result.get("success"):
                                        job_id = result["data"]["vendor_job_id"]
                                        st.success(f"Job created successfully! Job ID: {job_id}")
                                        st.info("You can check the results in the 'Check Results' tab.")
                                        
                                        # Add job_id to session state
                                        if "jobs" not in st.session_state:
                                            st.session_state.jobs = []
                                        st.session_state.jobs.append(job_id)
                                    else:
                                        st.error(f"Error creating job: {result.get('message', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")

elif page == "Check Results":
    st.title("Check Job Results")
    
    # Job ID input
    job_input_method = st.radio("Job ID Input Method", ["Enter Job ID", "Select from Recent Jobs"])
    
    job_id = None
    
    if job_input_method == "Enter Job ID":
        job_id = st.text_input("Job ID")
    else:
        if "jobs" in st.session_state and st.session_state.jobs:
            job_id = st.selectbox("Select a recent job", st.session_state.jobs)
        else:
            st.info("No recent jobs found. Please enter a Job ID manually.")
            job_id = st.text_input("Job ID")
    
    if job_id:
        if st.button("Get Results"):
            if not api_key:
                st.error("Please enter your API key in the sidebar.")
            else:
                with st.spinner("Getting job results..."):
                    result = get_job_results(api_key, job_id)
                    
                    if result.get("success"):
                        data = result["data"]
                        
                        # Display job information
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown("**Status**")
                            status = data.get("status", "unknown")
                            if status == "success":
                                st.success(status)
                            elif status == "processing":
                                st.info(status)
                            elif status == "cancelled":
                                st.warning(status)
                            else:
                                st.error(status)
                        
                        with col2:
                            st.markdown("**Completed**")
                            completed = data.get("completed", False)
                            if completed:
                                st.success("Yes")
                            else:
                                st.info("No")
                        
                        with col3:
                            st.markdown("**Created At**")
                            st.write(format_datetime(data.get("created_at", "")))
                        
                        with col4:
                            st.markdown("**Completed At**")
                            st.write(format_datetime(data.get("completed_at", "")))
                        
                        # Display statistics
                        st.markdown("### Statistics")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Products", data.get("total_deals", 0))
                        with col2:
                            st.metric("Completed", data.get("completed_deals", 0))
                        with col3:
                            st.metric("Failed", data.get("failed_deals", 0))
                        
                        # Display products
                        st.markdown("### Products")
                        products = data.get("products", [])
                        
                        if products:
                            for i, product in enumerate(products):
                                with st.expander(f"Product {i+1}: {product.get('name', 'Unknown Product')}"):
                                    col1, col2 = st.columns([1, 2])
                                    
                                    with col1:
                                        st.markdown("**Basic Information**")
                                        st.write(f"**ID:** {product.get('itemid', 'N/A')}")
                                        st.write(f"**Shop ID:** {product.get('shopid', 'N/A')}")
                                        st.write(f"**Price:** {product.get('price', 'N/A')} {product.get('currency', '')}")
                                        if product.get('price_before_discount'):
                                            st.write(f"**Original Price:** {product.get('price_before_discount')} {product.get('currency', '')}")
                                            st.write(f"**Discount:** {product.get('discount_percentage', 'N/A')}%")
                                        st.write(f"**Stock:** {product.get('stock', 'N/A')}")
                                        st.write(f"**Historical Sold:** {product.get('historical_sold', 'N/A')}")
                                        if product.get('monthly_sales'):
                                            st.write(f"**Monthly Sales:** {product.get('monthly_sales')}")
                                        st.write(f"**Brand:** {product.get('brand', 'N/A')}")
                                        st.write(f"**Model:** {product.get('model', 'N/A')}")
                                    
                                    with col2:
                                        st.markdown("**Description**")
                                        st.write(product.get('description', 'No description available'))
                                        
                                        # Display first image if available
                                        images = product.get('images', [])
                                        if images:
                                            st.markdown("**First Image**")
                                            st.image(images[0], width=300)
                                            if len(images) > 1:
                                                with st.expander(f"View all {len(images)} images"):
                                                    for img_url in images:
                                                        st.image(img_url, width=200)
                                    
                                    # Display attributes
                                    attributes = product.get('attributes', [])
                                    if attributes:
                                        st.markdown("**Attributes**")
                                        for attr in attributes:
                                            st.write(f"**{attr.get('name', 'N/A')}:** {attr.get('value', 'N/A')}")
                                    
                                    # Display seller information
                                    seller = product.get('seller', {})
                                    if seller:
                                        st.markdown("**Seller Information**")
                                        st.write(f"**Shop Name:** {seller.get('name', 'N/A')}")
                                        st.write(f"**Location:** {seller.get('location', 'N/A')}")
                                        st.write(f"**Rating:** {seller.get('rating', 'N/A')}")
                                        st.write(f"**Official Store:** {'Yes' if seller.get('is_official') else 'No'}")
                            
                            # Download JSON button
                            st.download_button(
                                label="Download All Data as JSON",
                                data=json.dumps(data, indent=2),
                                file_name=f"shopee_data_{job_id}.json",
                                mime="application/json"
                            )
                        else:
                            if data.get("completed", False):
                                st.info("No products found for this job.")
                            else:
                                st.info("Job is still processing. Please check back later.")
                                
                                # Show cancel button
                                if st.button("Cancel Job"):
                                    cancel_result = cancel_job(api_key, job_id)
                                    if cancel_result.get("success"):
                                        st.success("Job cancelled successfully!")
                                    else:
                                        st.error(f"Error cancelling job: {cancel_result.get('message', 'Unknown error')}")
                    else:
                        st.error(f"Error getting job results: {result.get('message', 'Unknown error')}")

elif page == "Documentation":
    st.title("API Documentation")
    
    st.markdown("""
    ## Overview
    The Shopee Data API allows you to extract detailed product information from Shopee Taiwan. 
    This interface provides access to the API functionality.
    
    ## Authentication
    All API requests require an API key for authentication. You can enter your API key in the sidebar.
    
    ## Workflow
    1. **Submit URLs**: Enter Shopee product URLs individually, in bulk, or via CSV upload.
    2. **Create Job**: The system processes your request as a background job.
    3. **Check Results**: View the extracted data once the job is complete.
    4. **Download Data**: Download the complete dataset in JSON format.
    
    ## URL Format
    The API accepts Shopee Taiwan URLs in the following format:
    ```
    https://shopee.tw/product-name-i.{shop_id}.{item_id}
    ```
    
    ## Data Extraction
    The API extracts comprehensive product data including:
    - Basic information (name, price, stock, etc.)
    - Detailed description
    - Product images
    - Attributes and specifications
    - Seller information
    - Ratings and reviews
    
    ## Rate Limits
    Please note that the API has rate limits:
    - 2,000 requests per hour per API key
    - Maximum of 10,000 products per job
    - Maximum of 50 concurrent jobs per user
    
    ## Support
    For API key requests or technical support, please contact our team at support@example.com.
    """)

# Footer
st.markdown("---")
st.markdown("© 2025 Your Company. All rights reserved.")
