<h2>Overview</h2>
<p>The Alzheimer's Detection Website is an intuitive platform designed to aid in the detection and classification of Alzheimer's disease using deep learning models. The site enables users to upload MRI scan images for analysis and provides reliable classification into categories such as:</p>
<ul>
    <li>Non-Demented</li>
    <li>Very Mild Demented</li>
    <li>Mild Demented</li>
    <li>Moderate Demented</li>
</ul>

<p>Additionally, the platform allows users to input medical data for classification, helping to determine whether a patient is likely to have Alzheimer's or not. This dual approach provides a comprehensive tool for early detection and monitoring of Alzheimer's disease progression.</p>

<p>This project serves as a tool to assist healthcare professionals and researchers in the early detection and monitoring of Alzheimer's disease progression. Additionally, the platform incorporates two distinct models:</p>
<ul>
    <li><strong>MRI Scan Model:</strong> This model analyzes MRI scan images and classifies them into the four stages of dementia: Non-Demented, Very Mild Demented, Mild Demented, and Moderate Demented.</li>
    <li><strong>Medical Data Model:</strong> This model takes in user medical data and provides a classification indicating whether the user is likely to have Alzheimer's or not.</li>
</ul>
<p>Furthermore, users can generate a detailed PDF report based on the medical data they provide, summarizing the analysis and classification results.</p>

<h2>Features</h2>
<ul>
    <li><strong>Image Upload:</strong> Users can easily upload MRI scan images for analysis.</li>
    <li><strong>Medical Data Input:</strong> Users can enter medical data (e.g., age, medical history, etc.) for analysis.</li>
    <li><strong>Classification Results:</strong> The site provides accurate classification results from both the MRI scan and medical data models.</li>
    <li><strong>PDF Generation:</strong> Based on the medical data provided, users can generate a detailed PDF report summarizing the classification results and analysis.</li>
    <li><strong>User-Friendly Interface:</strong> Built with Flask and Jinja2, the website is simple and intuitive to navigate.</li>
    <li><strong>Robust Models:</strong> Powered by deep learning models trained on an extensive dataset of MRI scans and medical data.</li>
</ul>

<h2>Dataset</h2>
<p>This project utilizes two distinct models, each with its own dataset:</p>

<h3>Model-1: Medical Data Model</h3>
<p>Model-1 uses a comprehensive medical dataset that contains health information for 2,149 patients, uniquely identified with IDs ranging from 4751 to 6900. The dataset includes demographic details, lifestyle factors, medical history, clinical measurements, cognitive and functional assessments, symptoms, and a diagnosis of Alzheimer's Disease. This dataset is ideal for researchers and data scientists looking to explore factors associated with Alzheimer's, develop predictive models, and conduct statistical analyses.</p>

<p>The dataset includes the following sections:</p>
<ul>
    <li><strong>Patient Information:</strong> Patient ID (ranging from 4751 to 6900)</li>
    <li><strong>Demographic Details:</strong> Age, Gender, Ethnicity, Education Level</li>
    <li><strong>Lifestyle Factors:</strong> BMI, Smoking, Alcohol Consumption, Physical Activity, Diet Quality, Sleep Quality</li>
    <li><strong>Medical History:</strong> Family History of Alzheimer's, Cardiovascular Disease, Diabetes, Depression, Head Injury, Hypertension</li>
    <li><strong>Clinical Measurements:</strong> Systolic and Diastolic Blood Pressure, Cholesterol Levels (Total, LDL, HDL, Triglycerides)</li>
    <li><strong>Cognitive and Functional Assessments:</strong> MMSE, Functional Assessment, Memory Complaints, Behavioral Problems, ADL</li>
    <li><strong>Symptoms:</strong> Confusion, Disorientation, Personality Changes, Difficulty Completing Tasks, Forgetfulness</li>
    <li><strong>Diagnosis Information:</strong> Diagnosis of Alzheimer's Disease (0 for No, 1 for Yes)</li>
</ul>

<p>The dataset can be found at the following link: 
<a href="https://www.kaggle.com/datasets/rabieelkharoua/alzheimers-disease-dataset/data">Medical Data Dataset on Kaggle</a></p>

<h3>Model-2: MRI Scan Image Model</h3>
<p>Model-2 uses a dataset of MRI scan images for classifying the severity of Alzheimer's Disease. The dataset consists of a total of 6400 images divided into four categories:</p>
<ul>
    <li><strong>Mild Demented:</strong> 896 images</li>
    <li><strong>Moderate Demented:</strong> 64 images</li>
    <li><strong>Very Mild Demented:</strong> 2240 images</li>
    <li><strong>Non-Demented:</strong> 3200 images</li>
</ul>
<p>To address the imbalance and reduce overfitting, data augmentation techniques were applied to expand the dataset. After augmentation, the total number of images increased to 12,072, with the following distribution:</p>
<ul>
    <li><strong>Mild Demented:</strong> 2961 images</li>
    <li><strong>Moderate Demented:</strong> 2748 images</li>
    <li><strong>Very Mild Demented:</strong> 3163 images</li>
    <li><strong>Non-Demented:</strong> 3200 images</li>
</ul>

<p>The dataset can be found at the following link: 
<a href="https://www.kaggle.com/datasets/raihannaufalramadhan/alzheimer-data">MRI Scan Dataset on Kaggle</a></p>

<h2>Technologies Used</h2>
<ul>
    <li><strong>Backend:</strong> Flask framework with Jinja2 template engine.</li>
    <li><strong>Frontend:</strong> HTML, CSS, and JavaScript.</li>
    <li><strong>Machine Learning:</strong> TensorFlow and Scikit-learn for model development.</li>
    <li><strong>Data Handling:</strong> Pandas and NumPy for data preprocessing.</li>
    <li><strong>PDF Generation:</strong> Python libraries such as FPDF for generating PDF reports based on medical data.</li>
</ul>



<h2>Usage</h2>
<ol>
    <li>Navigate to the website.</li>
    <li>Upload a MRI scan image in the supported format or input medical data.</li>
    <li>Click the "Analyze" button to classify the image or medical data.</li>
    <li>View the classification results on the results page. For MRI scans, the result will indicate the dementia stage, and for medical data, it will indicate Alzheimer's or Non-Alzheimer's status.</li>
    <li>If you provided medical data, you can generate a PDF report summarizing the analysis by clicking the "Generate PDF" button.</li>
</ol>

<h2>File Structure</h2>
<ul>
    <li><strong>app.py:</strong> Main Flask application file.</li>
    <li><strong>templates/:</strong> Contains HTML files for the website.</li>
    <li><strong>static/:</strong> Includes CSS, JavaScript, and image assets.</li>
    <li><strong>models/:</strong> Pre-trained deep learning models for MRI scan and medical data classification.</li>
    <li><strong>data/:</strong> Organized dataset for training and testing, including MRI scan images and medical records.</li>
</ul>


<h2>Contact</h2>
<p>For inquiries, please contact:</p>
<ul>
    <li><a href="mailto:first_email@example.com">btech10357.23@bitmesra.ac.in</a></li>
    <li><a href="mailto:second_email@example.com">btech10336.23@bitmesra.ac.in</a></li>
</ul>

<p><strong>Copyright Notice</strong></p>
<p>All rights are reserved by the author. Unauthorized use or distribution of this code is prohibited.</p>
