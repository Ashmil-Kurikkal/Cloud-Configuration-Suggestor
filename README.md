☁️ Autonimbus: Cloud Configuration Advisor
Intelligent Prototype for Weighted Cloud Instance Recommendation
Autonimbus is a proof-of-concept web application designed to help developers and system architects choose the most efficient and cost-effective cloud virtual machine (VM) instance for their specific workload.

Instead of relying solely on raw CPU and RAM numbers, Autonimbus employs a sophisticated weighting and multiplier algorithm to score instances based on an application's type, anticipated traffic, technical requirements, and the user's priority (Cost vs. Performance).

✨ Features
Intelligent Archetype Mapping: Automatically translates user-selected features (tags) or pre-defined projects (E-commerce, Data Analytics) into a required base specification (vCPU, RAM, Workload Pattern).

Traffic Scaling: Uses traffic multipliers (Low, Medium, High, Viral) to dynamically scale up the base vCPU and RAM requirements.

Suitability Scoring: Instances are pre-scored on categories like web_serving, database, caching, and analytics. These scores are weighted against the project's primary needs.

Priority Adjustment: Allows users to select a priority (Cost, Balanced, or Performance), which adjusts the final scoring algorithm to favor lower cost or higher raw performance.

Technical Filtering: Enables filtering by advanced criteria like NVMe SSD storage and High Network Performance (25+ Gbps).

Service Recommendations: Provides contextual suggestions for crucial additional services (CDN, Managed Databases, Load Balancers) based on the project's profile.

🛠️ Technology Stack
This prototype is built using a simple, modern stack to demonstrate the core recommendation logic.

Backend: Python with Flask

Handles the core recommendation logic (app.py).

Manages API endpoints (/recommend).

Database: SQLite (instances.db)

Stores cloud instance data (AWS, GCP, Azure) along with pre-calculated suitability scores.

Data Migration: Python Script (data_migration.py)

Loads raw instance data from JSON (instances.json) and transforms it into the structured SQLite database, assigning initial suitability weights.

Frontend: HTML5, CSS, and JavaScript

Provides a simple, multi-step questionnaire for capturing user requirements.

💡 How the Core Logic Works
The efficiency of Autonimbus lies in its calculate_instance_score function, which uses a combined metric:

Score=(Performance 
Weighted
​
 +Cost 
Weighted
​
 )×Category Suitability
Performance Score: Assesses vCPU and RAM fit against the derived minimum requirements, with different weighting applied based on the project's "Workload Pattern" (e.g., Memory Intensive favors RAM more than vCPU).

Cost Score: Normalizes the instance's monthly cost (calculated based on hourly rates) against the min/max cost of all eligible instances.

Priority Weights: Multiplies the Performance and Cost scores by user-defined weights (1.8 for priority, 0.5-1.0 for non-priority) to bias the results.

Category Suitability: Multiplies the combined score by how well the instance's type (e.g., Memory Optimized) aligns with the project's focus (e.g., Database workload).

🚀 Getting Started
Prerequisites
You need Python 3.x installed on your system.

Installation
Clone the repository:

git clone [repository_url]
cd Autonimbus

Install the required Python packages:

pip install -r requirements.txt

(Requires Flask and Flask-Cors)

Prepare the database:
The application relies on the instances.db file. Run the migration script once to populate it from instances.json.

python data_migration.py

Running the App
Start the Flask server:

python app.py

The application will typically run on http://127.0.0.1:5000.

Access the Web App:
Open your web browser and navigate to the address shown in your console (e.g., http://127.0.0.1:5000/).

🤝 Contribution
This is a prototype, and any suggestions for improving the weighting formulas, adding more cloud providers, or refining the application archetypes are welcome! Feel free to open an issue or submit a pull request.

Created with the power of Python and a belief in smarter cloud choices.
