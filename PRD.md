# Innergy Room Detection AI MVP - Product Requirements Document

**Project**: Innergy Room Detection AI - Blueprint Room Boundary Detection System  
**Goal**: Develop an AI-powered system that automatically detects and extracts room boundaries from architectural blueprints

**Note**: Authentication, multi-project management, and advanced blueprint formats (DWG/DXF) are intentionally excluded from MVP and will be addressed in Phase 2.

---

## Core Architecture (MVP)

**Single Blueprint Processing:**

- MVP features single blueprint upload and processing workflow
- NO multi-project management or saved blueprint library
- NO user accounts or authentication (can add JWT later)
- Single shared S3 bucket for temporary storage
- Future: Multi-user support, project management, blueprint versioning

**URL Structure:**

- `/` - Main upload and visualization interface
- `/results/:blueprintId` - View detection results for specific blueprint
- Simple client-side routing with React Router

---

## User Stories

### Primary User: Architects/Engineers (MVP Priority)

- As an architect, I want to **upload a blueprint image** so that I can automatically detect room boundaries
- As an engineer, I want to **see detected room boundaries overlaid on my blueprint** so that I can verify accuracy
- As a user, I want to **download detection results as JSON** so that I can integrate with other tools
- As a user, I want to **adjust detection confidence threshold** so that I can filter out low-quality predictions
- As a user, I want to **see processing status in real-time** so that I know when results are ready

**Note:** Focus on completing all primary user stories before addressing advanced features like batch processing or DWG file support.

### Secondary User: Construction Managers (Implement After Primary User)

- As a construction manager, I want to **export room measurements** so that I can estimate material costs
- As a project manager, I want to **compare multiple blueprint versions** so that I can track changes over time

---

## Key Features for MVP

### 1. Authentication System

**Must Have:**

- **NO authentication for MVP** - focus on core functionality
- Session tracking via browser sessionStorage
- Unique session IDs for tracking uploads

**Display Name Logic:**

- Anonymous users labeled as "User-{randomId}"
- Display name shown in UI header
- No persistence across sessions (MVP limitation)

**Success Criteria:**

- Users can access application without signup/login
- Each session has a unique identifier for tracking purposes

### 2. Blueprint Upload System

**Must Have:**

- Drag-and-drop file upload (PNG, JPG, PDF formats)
- File size limit: 10MB maximum
- Image preview before processing
- Upload progress indicator (0-100%)
- Support for single blueprint upload per session

**Upload Validation:**

- Accept only image formats: .png, .jpg, .jpeg, .pdf
- Display clear error messages for invalid formats
- Validate file size before upload
- Show image dimensions and file size after upload

**Success Criteria:**

- Upload completes within 5 seconds for typical blueprint (2-5MB)
- Preview renders correctly for all supported formats
- Error messages are clear and actionable
- Upload progress updates smoothly

### 3. AI-Powered Room Detection

**Must Have:**

- YOLOv5 model inference via AWS SageMaker endpoint
- Detection confidence threshold slider (0.3 to 0.9, default 0.5)
- Bounding box output with coordinates and confidence scores
- Processing time under 30 seconds for typical blueprint
- Visual feedback during processing (loading spinner + progress text)

**Detection Output Format:**

- JSON response with array of detected rooms
- Each room includes: `{x, y, width, height, confidence, class: 'room'}`
- Coordinates normalized to blueprint dimensions
- Filter results based on confidence threshold

**Success Criteria:**

- Model processes blueprints in under 30 seconds
- Detection accuracy ≥75% on test blueprints (measured manually)
- Confidence threshold filtering works correctly
- Results return in structured JSON format

### 4. Interactive Visualization

**Must Have:**

- **React-based canvas overlay** for blueprint display
- Render detected room boundaries as colored rectangles
- Unique color per detected room (randomly assigned)
- Hover tooltips showing room confidence score
- Zoom controls (25% to 400%)
- Pan functionality (click and drag)

**Boundary Display:**

- Rectangle overlays with 2px border width
- Semi-transparent fill (opacity 0.2) for room interior
- Confidence score badge in top-left corner of each room
- Color palette: 10 distinct colors with sufficient contrast

**Success Criteria:**

- Overlays render accurately over blueprint
- Hover interactions are smooth and responsive
- Zoom/pan controls maintain overlay alignment
- Confidence scores are clearly visible

### 5. Real-Time Processing Status

**Must Have:**

- WebSocket connection for live progress updates (optional for MVP)
- OR polling-based status checks every 2 seconds
- Progress stages: "Uploading" → "Processing" → "Analyzing" → "Complete"
- Estimated time remaining (based on average processing time)
- Error state handling with retry option

**Status Display:**

- Progress bar showing completion percentage
- Current stage label ("Uploading blueprint...")
- Estimated time remaining in seconds
- Cancel processing button (sets flag in Lambda)

**Success Criteria:**

- Status updates appear within 2 seconds
- Progress bar moves smoothly from 0% to 100%
- Error states display helpful messages
- Users can cancel long-running processes

### 6. Results Download & Export

**Must Have:**

- Download detection results as JSON file
- JSON includes blueprint metadata and all detected rooms
- Download annotated blueprint image (PNG) with overlays
- Export timestamp and session ID in metadata
- "Copy to Clipboard" button for JSON results

**Export Format:**

```json
{
  "blueprintId": "uuid-v4",
  "uploadedAt": "2025-11-07T10:30:00Z",
  "fileName": "floor-plan-1.png",
  "dimensions": {"width": 2048, "height": 1536},
  "detections": [
    {
      "roomId": 1,
      "boundingBox": {"x": 100, "y": 200, "width": 300, "height": 250},
      "confidence": 0.89,
      "class": "room"
    }
  ],
  "modelVersion": "yolov5-v1.0",
  "processingTime": 12.5
}
```

**Success Criteria:**

- JSON downloads immediately when button clicked
- Exported data includes all detected rooms
- Annotated image matches UI display exactly
- Clipboard copy works on all major browsers

### 7. AWS Lambda Orchestration

**Must Have:**

- **Upload Handler Lambda**: Receives blueprint, stores in S3, returns presigned URL
- **Inference Trigger Lambda**: Calls SageMaker endpoint with S3 image path
- **Results Formatter Lambda**: Processes model output, formats JSON response
- API Gateway integration for RESTful endpoints
- Error handling with 4xx/5xx status codes

**Lambda Functions:**

1. `POST /upload` - Handles file upload to S3
2. `POST /detect` - Triggers SageMaker inference
3. `GET /results/:blueprintId` - Retrieves detection results

**Success Criteria:**

- All Lambda functions execute in under 3 seconds (excluding model inference)
- API Gateway endpoints return proper status codes
- S3 presigned URLs work correctly
- Error responses include helpful debug information

### 8. SageMaker Model Deployment

**Must Have:**

- YOLOv5 model trained on blueprint dataset
- SageMaker endpoint with auto-scaling (1-3 instances)
- Model accepts image S3 path as input
- Returns bounding boxes in COCO format
- Endpoint latency under 25 seconds for inference

**Model Configuration:**

- Instance type: ml.m5.large (for MVP cost optimization)
- Input: Blueprint image from S3 (PNG/JPG)
- Output: JSON array of detections with confidence scores
- Batch size: 1 (single image processing)

**Success Criteria:**

- Model endpoint is accessible via API
- Inference completes in under 30 seconds
- Detection accuracy ≥75% on validation set
- Endpoint auto-scales during high load

### 9. State Persistence

**Must Have:**

- Store blueprint metadata in S3 (alongside image)
- Store detection results as JSON in S3
- Session-based caching in browser (sessionStorage)
- NO database required for MVP

**Data Storage:**

- S3 bucket structure: `/uploads/{sessionId}/{blueprintId}/`
  - `original.png` - Original blueprint
  - `metadata.json` - Upload timestamp, dimensions, filename
  - `results.json` - Detection output from model
  - `annotated.png` - Blueprint with overlays (optional)

**Success Criteria:**

- Uploaded blueprints persist in S3 for 7 days (lifecycle rule)
- Results can be retrieved via blueprintId
- Session data survives page refresh (via sessionStorage)
- No data loss during processing

### 10. Deployment

**Must Have:**

- React frontend deployed to S3 + CloudFront
- Lambda functions deployed via AWS SAM or Serverless Framework
- SageMaker endpoint running and accessible
- API Gateway with CORS enabled

**Success Criteria:**

- Frontend accessible via public URL
- API responds to requests from frontend domain
- Supports at least 10 concurrent users
- No crashes under normal load

---

## Data Model

### S3 Bucket Structure: `innergy-blueprints-dev` (Temporary Storage)

**Object Key Pattern:** `uploads/{sessionId}/{blueprintId}/`

```
uploads/
  session-abc123/
    blueprint-001/
      original.png
      metadata.json
      results.json
      annotated.png (optional)
```

**metadata.json Structure:**

```json
{
  "blueprintId": "uuid-v4",
  "sessionId": "session-abc123",
  "fileName": "floor-plan.png",
  "uploadedAt": "2025-11-07T10:30:00Z",
  "dimensions": {
    "width": 2048,
    "height": 1536
  },
  "fileSize": 4521890,
  "format": "png"
}
```

**results.json Structure:**

```json
{
  "blueprintId": "uuid-v4",
  "modelVersion": "yolov5-v1.0",
  "processingTime": 12.5,
  "detectedAt": "2025-11-07T10:30:15Z",
  "detections": [
    {
      "roomId": 1,
      "boundingBox": {
        "x": 100,
        "y": 200,
        "width": 300,
        "height": 250
      },
      "confidence": 0.89,
      "class": "room",
      "area": 75000
    }
  ],
  "statistics": {
    "totalRooms": 8,
    "avgConfidence": 0.82,
    "processingSteps": ["upload", "inference", "postprocess"]
  }
}
```

---

## Proposed Tech Stack

### Option 1: AWS Serverless Stack (Recommended for MVP)

**Frontend:**

- React + Vite
- React Router for navigation
- Konva.js or Canvas API for blueprint visualization
- Tailwind CSS for UI

**Backend:**

- AWS Lambda (Python 3.9) for orchestration
- API Gateway for REST endpoints
- Amazon S3 for blueprint storage
- AWS SageMaker for YOLOv5 model hosting

**ML Pipeline:**

- YOLOv5 (PyTorch) trained locally
- AWS SageMaker for model deployment
- Optional: AWS Textract for text extraction from blueprints

**Pros:**

- Fastest setup (serverless = no server management)
- Built-in scaling and high availability
- Pay-per-use pricing (low cost for MVP)
- Integrated with AWS ecosystem
- Simple deployment with SAM/Serverless Framework

**Cons:**

- AWS vendor lock-in
- Lambda cold starts (2-5 second delay on first request)
- SageMaker costs can be high with constant uptime
- Less control over infrastructure

**Pitfalls to Watch:**

- SageMaker endpoints charge hourly even when idle - use on-demand for MVP
- Lambda timeout limit is 15 minutes - ensure model inference completes faster
- S3 lifecycle policies needed to avoid storage costs piling up
- API Gateway throttling limits (10,000 requests/second by default)

---

### Option 2: Hybrid Stack (AWS + FastAPI)

**Frontend:**

- React + Vite
- Konva.js for visualization
- Tailwind CSS for UI

**Backend:**

- FastAPI (Python) on AWS EC2 or ECS
- PostgreSQL (AWS RDS) for metadata storage
- Amazon S3 for blueprint storage
- AWS SageMaker for model hosting

**Pros:**

- More control over backend logic
- FastAPI has excellent async performance
- Easier to add complex business logic
- Can run model locally during development

**Cons:**

- Requires server management (EC2/ECS)
- More complex deployment pipeline
- Higher baseline costs (EC2 instance always running)
- Need to handle scaling manually

**Pitfalls to Watch:**

- EC2 instance sizing - start small (t3.medium) and scale up
- Need to configure auto-scaling groups manually
- Database migrations and backup management
- SSL certificate setup for HTTPS

---

### Option 3: Fully Local Stack (Development/Demo)

**Frontend:**

- React + Vite
- Konva.js for visualization
- Tailwind CSS for UI

**Backend:**

- Flask or FastAPI (Python)
- SQLite for metadata storage
- Local file system for blueprint storage
- YOLOv5 running locally (CPU or GPU)

**Pros:**

- Complete control over architecture
- No cloud costs during development
- Fast iteration and debugging
- Can run entirely offline

**Cons:**

- Not production-ready
- No scalability
- Requires powerful local machine for model inference
- Manual deployment to cloud later

**Pitfalls to Watch:**

- YOLOv5 inference on CPU can be very slow (30-60 seconds)
- Need GPU (CUDA) for reasonable performance
- SQLite not suitable for concurrent users
- Local file storage doesn't scale

---

## Recommended Stack for MVP

**Frontend:** React + Vite + Konva.js + Tailwind CSS  
**Backend:** AWS Lambda (Python 3.9) + API Gateway + S3  
**ML Serving:** AWS SageMaker (YOLOv5 endpoint)  
**Deployment:** S3 + CloudFront (frontend), SAM/Serverless Framework (backend)

**Rationale:** AWS Serverless provides the fastest path to a working MVP with minimal infrastructure management. YOLOv5 on SageMaker is production-ready, and Lambda handles orchestration without server management. You can always migrate to a hybrid stack later if needed. For demo purposes, you can start with local YOLOv5 and migrate to SageMaker once the frontend is stable.

---

## Out of Scope for MVP

### Features NOT Included:

- **User Authentication** (AWS Cognito, JWT, or any login system)
- **Multi-User Support** (user accounts, permissions, roles)
- **Blueprint Library** (saved blueprints, project management, folders)
- **Batch Processing** (uploading multiple blueprints at once)
- **Advanced File Formats** (DWG, DXF, Revit files - only PNG/JPG/PDF)
- **Room Labeling** (manual annotation, room type classification)
- **Measurement Tools** (distance, area calculation beyond bounding box)
- **Version Control** (comparing blueprint revisions)
- **Collaboration Features** (sharing, comments, real-time editing)
- **Mobile App** (iOS/Android native apps)
- **Offline Mode** (PWA, service workers, offline processing)

### Technical Items NOT Included:

- **Advanced Model Training** (custom dataset labeling, hyperparameter tuning)
- **Model Versioning** (A/B testing, rollback mechanisms)
- **Analytics Dashboard** (usage metrics, detection accuracy tracking)
- **Automated Testing** (unit tests, integration tests - can add if time allows)
- **CI/CD Pipeline** (automated deployment via GitHub Actions)
- **Database** (DynamoDB, RDS, or any persistent storage beyond S3)
- **Caching Layer** (Redis, ElastiCache for faster retrieval)
- **WebSocket Support** (real-time progress updates - using polling instead)

---

## Known Limitations & Trade-offs

1. **No Authentication**: Anyone with the URL can upload blueprints (security risk in production - mitigated by making URL non-guessable)
2. **No Blueprint History**: Users cannot view previously uploaded blueprints (future: add DynamoDB for metadata storage)
3. **Single Blueprint Processing**: Cannot upload multiple blueprints in parallel (future: batch API endpoint)
4. **Limited File Formats**: Only PNG, JPG, PDF supported (future: add DWG/DXF converters)
5. **No Room Labeling**: Model only detects boundaries, not room types (future: multi-class YOLO model)
6. **Fixed Confidence Threshold**: Users can adjust but cannot train model (future: active learning pipeline)
7. **7-Day Storage Limit**: Blueprints auto-delete after 7 days via S3 lifecycle policy (cost optimization)
8. **No Concurrent Processing**: One blueprint per session at a time (future: job queue with SQS)

---

## Success Metrics for MVP Checkpoint

1. **Successfully upload and process** a blueprint in under 45 seconds (upload + inference)
2. **Page refresh** preserves session state (via sessionStorage)
3. **Detected room boundaries** render accurately on blueprint overlay
4. **Download JSON results** - file contains all detected rooms with confidence scores
5. **60 FPS rendering** maintained during zoom/pan interactions
6. **Deployed and accessible** via public URL (S3 + CloudFront)

---

## MVP Testing Checklist

### Core Functionality:

- [ ] User can upload a blueprint (PNG/JPG/PDF)
- [ ] User can see upload progress (0-100%)
- [ ] User can view processing status in real-time
- [ ] Detected rooms display as colored overlays

### Blueprint Processing:

- [ ] Can upload blueprint up to 10MB
- [ ] Upload fails gracefully for files >10MB
- [ ] Invalid file formats show clear error messages
- [ ] Processing completes within 45 seconds for typical blueprint
- [ ] Model returns bounding boxes in correct format

### Visualization & Interaction:

- [ ] Two browsers uploading simultaneously - both work independently
- [ ] User A uploads blueprint → sees detection results overlay
- [ ] User can zoom in/out (25% to 400%)
- [ ] User can pan across large blueprints
- [ ] Hover over room → shows confidence score tooltip
- [ ] Confidence threshold slider filters results in real-time

### Export & Download:

- [ ] User can download JSON results
- [ ] JSON file contains all detected rooms
- [ ] "Copy to Clipboard" button works in Chrome/Firefox/Safari
- [ ] Downloaded JSON is valid and parseable
- [ ] Annotated image download matches UI display

### Persistence:

- [ ] Page refresh retains sessionStorage data (blueprintId, results)
- [ ] Results can be retrieved via GET /results/:blueprintId
- [ ] S3 objects persist for 7 days, then auto-delete

### Performance:

- [ ] 60 FPS maintained during zoom/pan on canvas
- [ ] No lag during confidence threshold adjustment
- [ ] API responds within 3 seconds (excluding model inference)
- [ ] SageMaker inference completes in under 30 seconds

---

## Risk Mitigation

**Biggest Risk:** SageMaker cold start delays (15-30 seconds) on first request after idle period  
**Mitigation:** Use SageMaker on-demand endpoints for MVP (no hourly charges); add warming Lambda if needed; display clear "Model initializing..." message to users

**Second Risk:** YOLO model accuracy below 75% on real-world blueprints  
**Mitigation:** Start with YOLOv5 pretrained on COCO dataset; fine-tune on 100+ labeled blueprint images; provide confidence threshold slider so users can filter low-quality detections

**Third Risk:** Lambda timeout (15 min max) if model inference takes too long  
**Mitigation:** Process inference asynchronously via SageMaker; Lambda only orchestrates, doesn't wait for full response; poll status via separate endpoint

**Fourth Risk:** S3 storage costs grow rapidly with many uploads  
**Mitigation:** Set 7-day lifecycle policy to auto-delete old blueprints; compress images before storing; use S3 Intelligent-Tiering for cost optimization