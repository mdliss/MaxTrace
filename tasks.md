# Innergy Room Detection AI MVP - Development Task List

## Project File Structure

```
innergy-room-detection/
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload/
│   │   │   │   ├── DropZone.jsx
│   │   │   │   ├── FilePreview.jsx
│   │   │   │   └── UploadProgress.jsx
│   │   │   ├── Visualization/
│   │   │   │   ├── BlueprintCanvas.jsx
│   │   │   │   ├── RoomOverlay.jsx
│   │   │   │   └── ZoomControls.jsx
│   │   │   ├── Results/
│   │   │   │   ├── DetectionList.jsx
│   │   │   │   ├── ConfidenceSlider.jsx
│   │   │   │   └── ExportButtons.jsx
│   │   │   └── Layout/
│   │   │       ├── Header.jsx
│   │   │       ├── Sidebar.jsx
│   │   │       └── StatusBar.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── s3.js
│   │   │   ├── session.js
│   │   │   └── canvas.js
│   │   ├── hooks/
│   │   │   ├── useUpload.js
│   │   │   ├── useDetection.js
│   │   │   ├── useVisualization.js
│   │   │   └── useExport.js
│   │   ├── utils/
│   │   │   ├── constants.js
│   │   │   └── helpers.js
│   │   ├── contexts/
│   │   │   ├── UploadContext.jsx
│   │   │   └── DetectionContext.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── utils/
│   │   │   │   └── helpers.test.js
│   │   │   └── hooks/
│   │   │       └── useUpload.test.js
│   │   └── integration/
│   │       └── upload-detect-flow.test.js
│   ├── .env.development
│   ├── .env.production
│   ├── .gitignore
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── backend/
│   ├── lambda/
│   │   ├── upload_handler/
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   ├── detect_trigger/
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   └── results_fetcher/
│   │       ├── handler.py
│   │       └── requirements.txt
│   ├── sagemaker/
│   │   ├── model/
│   │   │   ├── yolov5_inference.py
│   │   │   ├── requirements.txt
│   │   │   └── best.pt (trained weights)
│   │   └── deploy_model.py
│   ├── tests/
│   │   ├── test_upload_handler.py
│   │   ├── test_detect_trigger.py
│   │   └── test_results_fetcher.py
│   ├── template.yaml (SAM template)
│   └── samconfig.toml
├── ml/
│   ├── data/
│   │   ├── train/
│   │   │   ├── images/
│   │   │   └── labels/
│   │   └── val/
│   │       ├── images/
│   │       └── labels/
│   ├── notebooks/
│   │   └── train_yolov5.ipynb
│   ├── scripts/
│   │   ├── prepare_dataset.py
│   │   └── evaluate_model.py
│   └── yolov5/ (cloned from ultralytics)
├── infrastructure/
│   ├── s3_lifecycle.json
│   ├── iam_policies.json
│   └── cloudfront_config.json
├── .gitignore
├── README.md
├── PRD.md
├── architecture.md
└── tasks.md (this file)
```

---

## PR #1: Project Setup & AWS Configuration

**Branch:** `setup/initial-config`  
**Goal:** Initialize frontend/backend projects with all dependencies and AWS services

### Tasks:

- [ ] **1.1: Initialize React + Vite Frontend**

  - Files to create: `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html`
  - Run: `npm create vite@latest frontend -- --template react`
  - Verify dev server runs: `cd frontend && npm run dev`

- [ ] **1.2: Install Frontend Dependencies**

  - Files to update: `frontend/package.json`
  - Install:
    ```bash
    npm install react-router-dom axios konva react-konva
    npm install -D tailwindcss postcss autoprefixer vitest @testing-library/react
    ```

- [ ] **1.3: Configure Tailwind CSS**

  - Files to create: `frontend/tailwind.config.js`, `frontend/postcss.config.js`
  - Files to update: `frontend/src/index.css`
  - Run: `npx tailwindcss init -p`
  - Add Tailwind directives to `index.css`:
    ```css
    @tailwind base;
    @tailwind components;
    @tailwind utilities;
    ```

- [ ] **1.4: Set Up AWS Resources**

  - Create S3 bucket: `innergy-blueprints-dev`
  - Enable S3 versioning and lifecycle policy (7-day auto-delete)
  - Create IAM role for Lambda functions (S3 + SageMaker permissions)
  - Set up API Gateway REST API
  - Files to create: `frontend/.env.development`, `frontend/.env.production`

- [ ] **1.5: Initialize AWS SAM Project**

  - Files to create: `backend/template.yaml`, `backend/samconfig.toml`
  - Run: `sam init --runtime python3.9 --name innergy-backend`
  - Define Lambda functions: UploadHandler, DetectTrigger, ResultsFetcher

- [ ] **1.6: Configure Git & .gitignore**

  - Files to create/update: `.gitignore`
  - Ignore: `node_modules/`, `.env*`, `dist/`, `__pycache__/`, `.aws-sam/`
  - Ensure `.env` files are ignored but `.env.example` is tracked

- [ ] **1.7: Create README with Setup Instructions**
  - Files to create: `README.md`
  - Include: Prerequisites, environment setup, AWS credentials, deployment steps

**PR Checklist:**

- [ ] Frontend dev server runs successfully
- [ ] Tailwind CSS classes work in test component
- [ ] AWS S3 bucket created with lifecycle policy
- [ ] SAM template validates: `sam validate`
- [ ] `.env.development` has all required API URLs

---

## PR #2: Frontend Upload System

**Branch:** `feature/upload-ui`  
**Goal:** Complete blueprint upload with drag-and-drop, validation, and progress tracking

### Tasks:

- [ ] **2.1: Create Upload Context**

  - Files to create: `frontend/src/contexts/UploadContext.jsx`
  - Provide: `uploadedFile`, `uploadProgress`, `blueprintId`, `sessionId`, `uploadStatus`, `uploadBlueprint()`, `resetUpload()`

- [ ] **2.2: Create Session Manager Service**

  - Files to create: `frontend/src/services/session.js`
  - Functions: `getSessionId()`, `saveSession(data)`, `clearSession()`
  - Use `sessionStorage` for persistence

- [ ] **2.3: Create Helper Functions**

  - Files to create: `frontend/src/utils/helpers.js`
  - Functions: `generateId()`, `formatBytes(bytes)`, `validateFile(file)`
  - Files to create: `frontend/src/utils/constants.js`
  - Constants: `MAX_FILE_SIZE = 10 * 1024 * 1024`, `ALLOWED_FORMATS = ['image/png', 'image/jpeg', 'application/pdf']`

- [ ] **2.4: Build DropZone Component**

  - Files to create: `frontend/src/components/Upload/DropZone.jsx`
  - Features: Drag-and-drop area, file input button, visual feedback on drag-over
  - Validation: File type, file size (max 10MB)
  - Handle errors gracefully with toast notifications

- [ ] **2.5: Build FilePreview Component**

  - Files to create: `frontend/src/components/Upload/FilePreview.jsx`
  - Display: Thumbnail, filename, file size, dimensions (if image)
  - Actions: "Remove" button to reset upload

- [ ] **2.6: Build UploadProgress Component**

  - Files to create: `frontend/src/components/Upload/UploadProgress.jsx`
  - Show: Progress bar (0-100%), current stage label ("Uploading...", "Processing...")
  - Cancel button (optional for MVP)

- [ ] **2.7: Create useUpload Hook**

  - Files to create: `frontend/src/hooks/useUpload.js`
  - Functions: `uploadBlueprint(file)`, track progress via Axios progress events
  - Return: `uploadProgress`, `error`, `isUploading`, `blueprintId`

- [ ] **2.8: Update App.jsx with Upload UI**
  - Files to update: `frontend/src/App.jsx`
  - Wrap app with UploadContext
  - Display DropZone, FilePreview, UploadProgress components
  - Basic routing: `/` (upload page), `/results/:blueprintId` (results page)

**PR Checklist:**

- [ ] Can drag-and-drop file onto DropZone
- [ ] Can select file via file input button
- [ ] Invalid file types show error message
- [ ] Files >10MB rejected with clear error
- [ ] FilePreview shows thumbnail and metadata
- [ ] UploadProgress shows 0-100% during upload
- [ ] sessionStorage persists blueprintId on page refresh

---

## PR #3: Backend Upload Lambda

**Branch:** `feature/upload-lambda`  
**Goal:** Implement Lambda function to handle uploads and generate S3 presigned URLs

### Tasks:

- [ ] **3.1: Create Upload Handler Lambda**

  - Files to create: `backend/lambda/upload_handler/handler.py`
  - Function: `lambda_handler(event, context)`
  - Operations:
    1. Validate request body (fileName, fileSize)
    2. Generate `blueprintId` (UUID v4)
    3. Create S3 presigned URL for PUT operation
    4. Store metadata.json in S3
  - Return: `{ blueprintId, presignedUrl, expiresIn }`

- [ ] **3.2: Add Dependencies**

  - Files to create: `backend/lambda/upload_handler/requirements.txt`
  - Add: `boto3`, `uuid`

- [ ] **3.3: Update SAM Template**

  - Files to update: `backend/template.yaml`
  - Define Lambda function: `UploadHandlerFunction`
  - API Gateway integration: `POST /upload`
  - Environment variables: `S3_BUCKET_NAME`, `PRESIGNED_URL_EXPIRY`

- [ ] **3.4: Create IAM Policy for S3 Access**

  - Files to create: `infrastructure/iam_policies.json`
  - Permissions: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` on bucket

- [ ] **3.5: Add Error Handling**

  - Files to update: `backend/lambda/upload_handler/handler.py`
  - Handle: Missing fields, invalid file types, S3 errors
  - Return proper HTTP status codes: 400, 500

- [ ] **3.6: Write Unit Tests**

  - Files to create: `backend/tests/test_upload_handler.py`
  - Test cases:
    - Valid upload request
    - Missing fileName in request
    - File size exceeds limit
    - S3 error handling

- [ ] **3.7: Deploy Lambda to AWS**
  - Run: `sam build && sam deploy --guided`
  - Test endpoint with Postman or curl
  - Verify presigned URL works for S3 upload

**PR Checklist:**

- [ ] Lambda function deploys successfully
- [ ] POST /upload returns presigned URL
- [ ] Presigned URL allows S3 PUT request
- [ ] metadata.json created in S3
- [ ] Error responses include helpful messages
- [ ] Unit tests pass: `pytest backend/tests/`

---

## PR #4: S3 Upload Service (Frontend)

**Branch:** `feature/s3-upload-service`  
**Goal:** Integrate frontend with Lambda to upload blueprints to S3

### Tasks:

- [ ] **4.1: Create API Client Service**

  - Files to create: `frontend/src/services/api.js`
  - Functions: `uploadBlueprint(file)` - POST to /upload endpoint
  - Use Axios with interceptors for error handling
  - Return: `{ blueprintId, presignedUrl, expiresIn }`

- [ ] **4.2: Create S3 Service**

  - Files to create: `frontend/src/services/s3.js`
  - Functions: `uploadToS3(presignedUrl, file, onProgress)`
  - Use Axios PUT with `onUploadProgress` callback
  - Track progress: `onProgress(progressEvent.loaded / progressEvent.total * 100)`

- [ ] **4.3: Update useUpload Hook**

  - Files to update: `frontend/src/hooks/useUpload.js`
  - Call `api.uploadBlueprint()` to get presigned URL
  - Call `s3.uploadToS3()` to upload file
  - Update `uploadProgress` state during upload
  - Store `blueprintId` in sessionStorage

- [ ] **4.4: Integrate Upload Flow in UI**

  - Files to update: `frontend/src/App.jsx`
  - Connect DropZone → useUpload → S3
  - Show UploadProgress during upload
  - Display success message with blueprintId on completion

- [ ] **4.5: Add Error Handling**

  - Files to update: `frontend/src/services/api.js`, `frontend/src/hooks/useUpload.js`
  - Handle: Network errors, S3 upload failures, expired presigned URLs
  - Show user-friendly error messages

- [ ] **4.6: Test Upload Flow End-to-End**
  - Manually test: Select file → Upload → Verify S3 object created
  - Check: S3 console for `original.png` and `metadata.json`

**PR Checklist:**

- [ ] Frontend calls POST /upload successfully
- [ ] Presigned URL received from Lambda
- [ ] File uploaded to S3 via presigned URL
- [ ] Upload progress updates in real-time (0-100%)
- [ ] S3 objects persist after upload (original.png, metadata.json)
- [ ] Error messages display on upload failure

---

## PR #5: YOLOv5 Model Training & Deployment

**Branch:** `feature/yolo-model`  
**Goal:** Train YOLOv5 on blueprint dataset and deploy to SageMaker

### Tasks:

- [ ] **5.1: Prepare Blueprint Dataset**

  - Files to create: `ml/data/train/`, `ml/data/val/`
  - Collect 100+ labeled blueprint images (COCO format)
  - Split: 80% train, 20% validation
  - Labels: Room bounding boxes in YOLO format (normalized x, y, width, height)

- [ ] **5.2: Clone YOLOv5 Repository**

  - Run: `git clone https://github.com/ultralytics/yolov5 ml/yolov5`
  - Install dependencies: `pip install -r ml/yolov5/requirements.txt`

- [ ] **5.3: Train YOLOv5 Model**

  - Files to create: `ml/notebooks/train_yolov5.ipynb`
  - Run training:
    ```bash
    python ml/yolov5/train.py \
      --data dataset.yaml \
      --weights yolov5s.pt \
      --epochs 50 \
      --batch 16 \
      --img 640
    ```
  - Save best weights: `ml/sagemaker/model/best.pt`

- [ ] **5.4: Create SageMaker Inference Script**

  - Files to create: `ml/sagemaker/model/yolov5_inference.py`
  - Functions: `model_fn(model_dir)`, `predict_fn(input_data, model)`
  - Input: S3 image path
  - Output: JSON array of bounding boxes (COCO format)

- [ ] **5.5: Create SageMaker Deployment Script**

  - Files to create: `ml/sagemaker/deploy_model.py`
  - Operations:
    1. Create SageMaker model from trained weights
    2. Create endpoint configuration (ml.m5.large, auto-scaling 1-3 instances)
    3. Deploy endpoint: `yolov5-blueprint-detector`

- [ ] **5.6: Test Model Locally**

  - Files to create: `ml/scripts/evaluate_model.py`
  - Run inference on validation set
  - Calculate mAP (mean Average Precision) - target: >0.75

- [ ] **5.7: Deploy Model to SageMaker**
  - Run: `python ml/sagemaker/deploy_model.py`
  - Verify endpoint is active in SageMaker console
  - Test inference with sample blueprint

**PR Checklist:**

- [ ] YOLOv5 model trained on blueprint dataset
- [ ] Model achieves >75% mAP on validation set
- [ ] SageMaker endpoint deployed successfully
- [ ] Endpoint responds to test inference request
- [ ] Inference latency <30 seconds

---

## PR #6: Detection Trigger Lambda

**Branch:** `feature/detection-lambda`  
**Goal:** Lambda to invoke SageMaker endpoint and store results

### Tasks:

- [ ] **6.1: Create Detect Trigger Lambda**

  - Files to create: `backend/lambda/detect_trigger/handler.py`
  - Function: `lambda_handler(event, context)`
  - Operations:
    1. Parse blueprintId from request body
    2. Read blueprint from S3 (original.png)
    3. Invoke SageMaker endpoint with image S3 path
    4. Parse model output (bounding boxes)
    5. Store results.json in S3
  - Return: `{ blueprintId, status: "processing", estimatedTime: 25 }`

- [ ] **6.2: Add Dependencies**

  - Files to create: `backend/lambda/detect_trigger/requirements.txt`
  - Add: `boto3`, `json`

- [ ] **6.3: Update SAM Template**

  - Files to update: `backend/template.yaml`
  - Define Lambda function: `DetectTriggerFunction`
  - API Gateway integration: `POST /detect`
  - Environment variables: `S3_BUCKET_NAME`, `SAGEMAKER_ENDPOINT`

- [ ] **6.4: Add IAM Permissions**

  - Files to update: `infrastructure/iam_policies.json`
  - Add: `sagemaker:InvokeEndpoint` permission

- [ ] **6.5: Handle SageMaker Errors**

  - Files to update: `backend/lambda/detect_trigger/handler.py`
  - Handle: Endpoint timeout, model errors, invalid output
  - Store error state in results.json if inference fails

- [ ] **6.6: Write Unit Tests**

  - Files to create: `backend/tests/test_detect_trigger.py`
  - Test cases:
    - Valid detection request
    - SageMaker endpoint unavailable
    - Invalid blueprintId

- [ ] **6.7: Deploy Lambda**
  - Run: `sam build && sam deploy`
  - Test endpoint with sample blueprintId

**PR Checklist:**

- [ ] Lambda function deploys successfully
- [ ] POST /detect triggers SageMaker inference
- [ ] results.json stored in S3 with bounding boxes
- [ ] Error handling works for SageMaker failures
- [ ] Unit tests pass

---

## PR #7: Results Retrieval Lambda

**Branch:** `feature/results-lambda`  
**Goal:** Lambda to fetch and format detection results from S3

### Tasks:

- [ ] **7.1: Create Results Fetcher Lambda**

  - Files to create: `backend/lambda/results_fetcher/handler.py`
  - Function: `lambda_handler(event, context)`
  - Operations:
    1. Parse blueprintId from path parameter
    2. Fetch results.json from S3
    3. Fetch metadata.json from S3
    4. Combine and format response

- [ ] **7.2: Update SAM Template**

  - Files to update: `backend/template.yaml`
  - Define Lambda function: `ResultsFetcherFunction`
  - API Gateway integration: `GET /results/{blueprintId}`

- [ ] **7.3: Add Response Formatting**

  - Files to update: `backend/lambda/results_fetcher/handler.py`
  - Format response:
    ```json
    {
      "blueprintId": "...",
      "detections": [...],
      "metadata": {...},
      "processingTime": 12.5
    }
    ```

- [ ] **7.4: Handle Missing Results**

  - Files to update: `backend/lambda/results_fetcher/handler.py`
  - Return 404 if blueprintId not found
  - Return 202 if processing still in progress

- [ ] **7.5: Write Unit Tests**

  - Files to create: `backend/tests/test_results_fetcher.py`
  - Test cases:
    - Valid results retrieval
    - Blueprint not found (404)
    - Processing in progress (202)

- [ ] **7.6: Deploy Lambda**
  - Run: `sam build && sam deploy`
  - Test endpoint with existing blueprintId

**PR Checklist:**

- [ ] Lambda function deploys successfully
- [ ] GET /results/:blueprintId returns detection results
- [ ] 404 returned for non-existent blueprintId
- [ ] 202 returned if processing incomplete
- [ ] Unit tests pass

---

## PR #8: Frontend Detection & Polling

**Branch:** `feature/detection-ui`  
**Goal:** Trigger detection from frontend and poll for results

### Tasks:

- [ ] **8.1: Create Detection Context**

  - Files to create: `frontend/src/contexts/DetectionContext.jsx`
  - Provide: `detections`, `confidenceThreshold`, `processingStatus`, `triggerDetection()`, `updateThreshold()`, `filterDetections()`

- [ ] **8.2: Create useDetection Hook**

  - Files to create: `frontend/src/hooks/useDetection.js`
  - Functions: `triggerDetection(blueprintId)` - POST to /detect
  - Poll GET /results/:blueprintId every 2 seconds until complete
  - Return: `detections`, `isProcessing`, `processingStatus`, `error`

- [ ] **8.3: Build StatusBar Component**

  - Files to create: `frontend/src/components/Layout/StatusBar.jsx`
  - Display: Processing status ("Uploading", "Processing", "Analyzing", "Complete")
  - Show progress bar (estimate based on average time)
  - Display errors if detection fails

- [ ] **8.4: Add "Detect Rooms" Button**

  - Files to update: `frontend/src/App.jsx`
  - Enable button after successful upload
  - Trigger `useDetection.triggerDetection(blueprintId)`
  - Show StatusBar during processing

- [ ] **8.5: Handle Polling Logic**

  - Files to update: `frontend/src/hooks/useDetection.js`
  - Poll every 2 seconds: `setInterval(() => fetchResults(), 2000)`
  - Stop polling when status is "complete" or "error"
  - Clear interval on component unmount

- [ ] **8.6: Display Results Summary**

  - Files to create: `frontend/src/components/Results/DetectionList.jsx`
  - Show: Total rooms detected, average confidence
  - List each room with confidence score

- [ ] **8.7: Add Confidence Threshold Slider**
  - Files to create: `frontend/src/components/Results/ConfidenceSlider.jsx`
  - Range: 0.3 to 0.9, default 0.5
  - Filter detections below threshold in real-time

**PR Checklist:**

- [ ] "Detect Rooms" button triggers detection
- [ ] StatusBar shows processing status in real-time
- [ ] Polling stops when results are ready
- [ ] DetectionList displays all detected rooms
- [ ] ConfidenceSlider filters results dynamically
- [ ] Error states handled gracefully

---

## PR #9: Blueprint Visualization with Konva.js

**Branch:** `feature/canvas-visualization`  
**Goal:** Render blueprint with room boundary overlays on HTML5 canvas

### Tasks:

- [ ] **9.1: Create Canvas Renderer Service**

  - Files to create: `frontend/src/services/canvas.js`
  - Functions: `renderBlueprint(imageUrl, stageRef)`, `renderOverlays(detections, stageRef)`, `applyTransform(zoom, pan, stageRef)`

- [ ] **9.2: Build BlueprintCanvas Component**

  - Files to create: `frontend/src/components/Visualization/BlueprintCanvas.jsx`
  - Use Konva Stage and Layer
  - Load blueprint image from S3
  - Render image on canvas at actual size

- [ ] **9.3: Build RoomOverlay Component**

  - Files to create: `frontend/src/components/Visualization/RoomOverlay.jsx`
  - Render bounding boxes as Konva Rectangles
  - Assign unique color per room (palette of 10 colors)
  - Semi-transparent fill (opacity 0.2)
  - Confidence badge in top-left corner

- [ ] **9.4: Add Hover Tooltips**

  - Files to update: `frontend/src/components/Visualization/RoomOverlay.jsx`
  - Show confidence score on hover
  - Highlight room border on hover (increase opacity)

- [ ] **9.5: Build ZoomControls Component**

  - Files to create: `frontend/src/components/Visualization/ZoomControls.jsx`
  - Buttons: Zoom In (+25%), Zoom Out (-25%), Reset (100%)
  - Slider: 25% to 400%
  - Display current zoom level

- [ ] **9.6: Implement Pan Functionality**

  - Files to update: `frontend/src/components/Visualization/BlueprintCanvas.jsx`
  - Click and drag to pan across blueprint
  - Constrain pan to blueprint boundaries

- [ ] **9.7: Create useVisualization Hook**

  - Files to create: `frontend/src/hooks/useVisualization.js`
  - State: `zoomLevel`, `panOffset`
  - Functions: `handleZoom(delta)`, `handlePan(dx, dy)`, `resetView()`

- [ ] **9.8: Optimize Rendering Performance**
  - Files to update: `frontend/src/services/canvas.js`
  - Use Konva layers: blueprint layer (static), overlay layer (dynamic)
  - Cache blueprint image to avoid reloading
  - Throttle pan events to maintain 60 FPS

**PR Checklist:**

- [ ] Blueprint image renders on canvas
- [ ] Room overlays display with correct coordinates
- [ ] Each room has a unique color
- [ ] Hover tooltips show confidence scores
- [ ] Zoom controls work (25%-400%)
- [ ] Pan by dragging works smoothly
- [ ] 60 FPS maintained during interactions

---

## PR #10: Export & Download Features

**Branch:** `feature/export-results`  
**Goal:** Allow users to download detection results as JSON and annotated images

### Tasks:

- [ ] **10.1: Create useExport Hook**

  - Files to create: `frontend/src/hooks/useExport.js`
  - Functions: `downloadJSON()`, `downloadAnnotatedImage()`, `copyToClipboard()`

- [ ] **10.2: Implement JSON Download**

  - Files to update: `frontend/src/hooks/useExport.js`
  - Format detections as JSON:
    ```json
    {
      "blueprintId": "...",
      "detections": [...],
      "metadata": {...}
    }
    ```
  - Create Blob from JSON string
  - Trigger browser download with filename: `{blueprintId}-detections.json`

- [ ] **10.3: Implement Copy to Clipboard**

  - Files to update: `frontend/src/hooks/useExport.js`
  - Use `navigator.clipboard.writeText(JSON.stringify(detections))`
  - Show toast notification: "Copied to clipboard!"

- [ ] **10.4: Build ExportButtons Component**

  - Files to create: `frontend/src/components/Results/ExportButtons.jsx`
  - Buttons: "Download JSON", "Copy to Clipboard", "Download Image" (optional)
  - Disable buttons if no detections available

- [ ] **10.5: Implement Annotated Image Download (Optional)**

  - Files to update: `frontend/src/hooks/useExport.js`
  - Export canvas as PNG using `stage.toDataURL()`
  - Trigger download with filename: `{blueprintId}-annotated.png`

- [ ] **10.6: Integrate Export UI**
  - Files to update: `frontend/src/App.jsx`
  - Add ExportButtons component to Sidebar
  - Enable buttons only when detections are available

**PR Checklist:**

- [ ] "Download JSON" button downloads results file
- [ ] JSON file is valid and parseable
- [ ] "Copy to Clipboard" button works in Chrome/Firefox/Safari
- [ ] Toast notification shows on successful copy
- [ ] (Optional) "Download Image" exports annotated blueprint

---

## PR #11: Deployment & Infrastructure

**Branch:** `deploy/production`  
**Goal:** Deploy frontend to S3/CloudFront and backend to AWS

### Tasks:

- [ ] **11.1: Build Frontend for Production**

  - Run: `cd frontend && npm run build`
  - Output: `frontend/dist/` directory
  - Verify bundle size: <500KB gzipped

- [ ] **11.2: Create S3 Bucket for Frontend**

  - Bucket name: `innergy-frontend-prod`
  - Enable static website hosting
  - Set index document: `index.html`

- [ ] **11.3: Upload Frontend to S3**

  - Run: `aws s3 sync frontend/dist/ s3://innergy-frontend-prod --delete`
  - Verify: Access S3 website URL in browser

- [ ] **11.4: Configure CloudFront Distribution**

  - Files to create: `infrastructure/cloudfront_config.json`
  - Origin: S3 bucket (innergy-frontend-prod)
  - Caching: 24 hours for static assets
  - HTTPS: Required (SSL certificate via ACM)

- [ ] **11.5: Deploy Backend with SAM**

  - Run: `cd backend && sam build && sam deploy --guided`
  - Stack name: `innergy-backend-prod`
  - Verify Lambda functions deployed

- [ ] **11.6: Set Up S3 Lifecycle Policy**

  - Files to create: `infrastructure/s3_lifecycle.json`
  - Rule: Auto-delete objects in `innergy-blueprints-dev` after 7 days
  - Apply policy: `aws s3api put-bucket-lifecycle-configuration --bucket innergy-blueprints-dev --lifecycle-configuration file://s3_lifecycle.json`

- [ ] **11.7: Update Frontend Environment Variables**

  - Files to update: `frontend/.env.production`
  - Set: `VITE_API_GATEWAY_URL=https://api.innergy-ai.com/v1`
  - Rebuild and redeploy frontend

- [ ] **11.8: Test Production Deployment**
  - Upload a blueprint via CloudFront URL
  - Trigger detection and verify results
  - Test with multiple browsers (Chrome, Firefox, Safari)
  - Load test with 10 concurrent users (optional)

**PR Checklist:**

- [ ] Frontend deployed to S3 + CloudFront
- [ ] Backend Lambdas deployed and accessible
- [ ] SageMaker endpoint running and responsive
- [ ] S3 lifecycle policy active (7-day auto-delete)
- [ ] HTTPS enabled on CloudFront
- [ ] Production URL accessible: https://innergy-ai.cloudfront.net

---

## PR #12: Testing & Documentation

**Branch:** `test/comprehensive-testing`  
**Goal:** Add unit tests, integration tests, and update documentation

### Tasks:

- [ ] **12.1: Write Frontend Unit Tests**

  - Files to create: `frontend/tests/unit/utils/helpers.test.js`
  - Test: `generateId()`, `formatBytes()`, `validateFile()`
  - Files to create: `frontend/tests/unit/hooks/useUpload.test.js`
  - Test: Upload progress tracking, error handling

- [ ] **12.2: Write Backend Unit Tests**

  - Files to update: `backend/tests/test_upload_handler.py`
  - Test all Lambda functions with mocked AWS services (moto library)
  - Coverage target: >80%

- [ ] **12.3: Write Integration Tests**

  - Files to create: `frontend/tests/integration/upload-detect-flow.test.js`
  - Test end-to-end flow: Upload → Detect → Results → Export
  - Use Vitest + React Testing Library

- [ ] **12.4: Update README**

  - Files to update: `README.md`
  - Add: Project overview, tech stack, setup instructions, deployment guide
  - Include: Screenshots, API documentation, troubleshooting

- [ ] **12.5: Add API Documentation**

  - Files to create: `docs/API.md`
  - Document all endpoints: POST /upload, POST /detect, GET /results/:blueprintId
  - Include: Request/response examples, error codes

- [ ] **12.6: Performance Testing**

  - Test upload with 10MB files
  - Test detection with complex blueprints (20+ rooms)
  - Measure: Upload time, inference time, rendering FPS
  - **Status:** Needs manual testing

- [ ] **12.7: Cross-Browser Testing**
  - Test in Chrome, Firefox, Safari, Edge
  - Fix compatibility issues (if any)
  - **Status:** Needs manual testing

**PR Checklist:**

- [ ] Unit tests pass: `npm run test` (frontend), `pytest` (backend)
- [ ] Integration tests cover main user flows
- [ ] README has clear setup instructions
- [ ] API documentation is complete
- [ ] Performance meets targets (<45s total processing time)

---

## MVP Completion Checklist

### Required Features:

- [ ] Blueprint upload (PNG/JPG/PDF, max 10MB)
- [ ] YOLOv5 detection with SageMaker endpoint
- [ ] Room boundary overlays on blueprint canvas
- [ ] Confidence threshold filtering (0.3-0.9)
- [ ] Download JSON results
- [ ] Copy results to clipboard
- [ ] Real-time processing status updates (polling)
- [ ] Session persistence (sessionStorage)
- [ ] Deployed to production (S3 + CloudFront + Lambda + SageMaker)

### Performance Targets:

- [ ] Upload time <5s for 5MB blueprint
- [ ] SageMaker inference <30s (warm start)
- [ ] Total processing time <45s (upload → detection → results)
- [ ] 60 FPS during canvas zoom/pan
- [ ] API response time <3s (excluding ML inference)

### Testing Scenarios:

- [ ] Upload 10MB blueprint successfully
- [ ] Upload fails gracefully for files >10MB
- [ ] Invalid file formats rejected with clear error
- [ ] Detection completes in <45 seconds
- [ ] Overlays render accurately on blueprint
- [ ] Confidence slider filters results in real-time
- [ ] JSON download contains all detections
- [ ] Page refresh preserves session state (blueprintId)
- [ ] 10 concurrent users tested without degradation

---

## Post-MVP: Phase 2 Preparation

**Next PRs (After MVP Deadline):**

- PR #13: User Authentication (AWS Cognito)
- PR #14: Blueprint Library (DynamoDB storage)
- PR #15: Batch Processing (multiple uploads)
- PR #16: Advanced File Formats (DWG/DXF support)
- PR #17: Room Type Classification (multi-class YOLO)
- PR #18: Measurement Tools (area calculation, distance)
- PR #19: WebSocket Status Updates (replace polling)
- PR #20: Model Versioning & A/B Testing