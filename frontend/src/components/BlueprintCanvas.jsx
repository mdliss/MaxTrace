import { useRef, useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Stage, Layer, Image as KonvaImage, Rect, Text } from 'react-konva';
import useImage from 'use-image';

// Color palette for room boundaries (10 distinct colors)
const ROOM_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
  '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B88B', '#B8E6B8'
];

const BlueprintCanvas = forwardRef(({ imageUrl, detections = [], confidenceThreshold = 0.5 }, ref) => {
  const stageRef = useRef(null);
  const [image] = useImage(imageUrl);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [hoveredRoom, setHoveredRoom] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Filter detections by confidence threshold
  const filteredDetections = detections.filter(d => d.confidence >= confidenceThreshold);

  // Calculate canvas dimensions based on container
  useEffect(() => {
    const updateDimensions = () => {
      const container = stageRef.current?.container();
      if (container) {
        setDimensions({
          width: container.offsetWidth,
          height: container.offsetHeight
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Center image when loaded
  useEffect(() => {
    if (image && dimensions.width && dimensions.height) {
      const scaleX = dimensions.width / image.width;
      const scaleY = dimensions.height / image.height;
      const initialScale = Math.min(scaleX, scaleY, 1);

      setScale(initialScale);
      setPosition({
        x: (dimensions.width - image.width * initialScale) / 2,
        y: (dimensions.height - image.height * initialScale) / 2
      });
    }
  }, [image, dimensions]);

  const handleWheel = (e) => {
    e.evt.preventDefault();

    const stage = stageRef.current;
    const oldScale = scale;
    const pointer = stage.getPointerPosition();

    const mousePointTo = {
      x: (pointer.x - position.x) / oldScale,
      y: (pointer.y - position.y) / oldScale,
    };

    // Zoom limits: 25% to 400%
    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const newScale = Math.max(0.25, Math.min(4, oldScale + direction * 0.1));

    setScale(newScale);
    setPosition({
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y - mousePointTo.y * newScale,
    });
  };

  const handleDragEnd = (e) => {
    setPosition({
      x: e.target.x(),
      y: e.target.y(),
    });
  };

  const resetView = () => {
    if (image && dimensions.width && dimensions.height) {
      const scaleX = dimensions.width / image.width;
      const scaleY = dimensions.height / image.height;
      const initialScale = Math.min(scaleX, scaleY, 1);

      setScale(initialScale);
      setPosition({
        x: (dimensions.width - image.width * initialScale) / 2,
        y: (dimensions.height - image.height * initialScale) / 2
      });
    }
  };

  const zoomIn = () => {
    const newScale = Math.min(4, scale + 0.2);
    setScale(newScale);
  };

  const zoomOut = () => {
    const newScale = Math.max(0.25, scale - 0.2);
    setScale(newScale);
  };

  const exportAsImage = (filename = 'annotated-blueprint.png') => {
    if (!stageRef.current) return;

    // Temporarily reset position and scale for clean export
    const currentPosition = { ...position };
    const currentScale = scale;

    // Reset to fit view
    if (image && dimensions.width && dimensions.height) {
      const scaleX = dimensions.width / image.width;
      const scaleY = dimensions.height / image.height;
      const exportScale = Math.min(scaleX, scaleY, 1);

      const stage = stageRef.current;
      stage.position({
        x: (dimensions.width - image.width * exportScale) / 2,
        y: (dimensions.height - image.height * exportScale) / 2
      });
      stage.scale({ x: exportScale, y: exportScale });

      // Export the stage as image
      const dataURL = stage.toDataURL({
        pixelRatio: 2, // Higher quality export
        mimeType: 'image/png'
      });

      // Restore original view
      stage.position(currentPosition);
      stage.scale({ x: currentScale, y: currentScale });

      // Trigger download
      const link = document.createElement('a');
      link.download = filename;
      link.href = dataURL;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Expose export function via ref
  useImperativeHandle(ref, () => ({
    exportAsImage
  }), [image, dimensions, position, scale, filteredDetections]);

  return (
    <div className="relative w-full h-full">
      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col gap-2 bg-white rounded-lg shadow-lg p-2">
        <button
          onClick={zoomIn}
          className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={resetView}
          className="px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors text-xs"
          title="Reset View"
        >
          ⟲
        </button>
        <button
          onClick={zoomOut}
          className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          title="Zoom Out"
        >
          −
        </button>
        <div className="text-xs text-center text-gray-600 mt-1">
          {Math.round(scale * 100)}%
        </div>
      </div>

      {/* Stats Display */}
      {filteredDetections.length > 0 && (
        <div className="absolute top-4 left-4 z-10 bg-white rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-gray-800">
            Rooms Detected: {filteredDetections.length}
          </p>
          <p className="text-xs text-gray-600">
            Avg Confidence: {(filteredDetections.reduce((sum, d) => sum + d.confidence, 0) / filteredDetections.length * 100).toFixed(1)}%
          </p>
        </div>
      )}

      {/* Canvas */}
      <div className="w-full h-full bg-gray-100">
        <Stage
          ref={stageRef}
          width={dimensions.width}
          height={dimensions.height}
          onWheel={handleWheel}
          draggable
          x={position.x}
          y={position.y}
          scaleX={scale}
          scaleY={scale}
          onDragEnd={handleDragEnd}
        >
          <Layer>
            {/* Blueprint Image */}
            {image && <KonvaImage image={image} />}

            {/* Room Boundary Overlays */}
            {filteredDetections.map((detection, index) => {
              const color = ROOM_COLORS[index % ROOM_COLORS.length];
              const { x, y, width, height } = detection.boundingBox;
              const isHovered = hoveredRoom === detection.roomId;

              return (
                <Rect
                  key={detection.roomId}
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  stroke={color}
                  strokeWidth={2}
                  fill={color}
                  opacity={isHovered ? 0.3 : 0.2}
                  onMouseEnter={() => setHoveredRoom(detection.roomId)}
                  onMouseLeave={() => setHoveredRoom(null)}
                />
              );
            })}

            {/* Confidence Score Badges */}
            {filteredDetections.map((detection, index) => {
              const color = ROOM_COLORS[index % ROOM_COLORS.length];
              const { x, y } = detection.boundingBox;
              const confidencePercent = Math.round(detection.confidence * 100);

              return (
                <Text
                  key={`label-${detection.roomId}`}
                  x={x + 5}
                  y={y + 5}
                  text={`${confidencePercent}%`}
                  fontSize={14}
                  fontStyle="bold"
                  fill={color}
                  stroke="white"
                  strokeWidth={3}
                  shadowColor="black"
                  shadowBlur={5}
                  shadowOpacity={0.3}
                />
              );
            })}
          </Layer>
        </Stage>
      </div>

      {/* Hover Tooltip */}
      {hoveredRoom && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10 bg-black bg-opacity-80 text-white rounded-lg px-4 py-2 pointer-events-none">
          {(() => {
            const room = filteredDetections.find(d => d.roomId === hoveredRoom);
            return room ? (
              <>
                <p className="text-sm font-semibold">Room {room.roomId}</p>
                <p className="text-xs">Confidence: {(room.confidence * 100).toFixed(1)}%</p>
                <p className="text-xs">Area: {room.area?.toLocaleString()} px²</p>
              </>
            ) : null;
          })()}
        </div>
      )}
    </div>
  );
});

BlueprintCanvas.displayName = 'BlueprintCanvas';

export default BlueprintCanvas;
