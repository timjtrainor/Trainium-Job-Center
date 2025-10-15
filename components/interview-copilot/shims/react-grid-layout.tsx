import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

type Breakpoint = 'lg' | 'md' | 'sm';

export interface LayoutItem {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    minW?: number;
    maxW?: number;
    minH?: number;
    maxH?: number;
    static?: boolean;
}

export type Layout = LayoutItem;

export type Layouts = Partial<Record<Breakpoint, Layout[]>>;

type Margin = [number, number];

type Padding = [number, number];

type BreakpointCols = Record<Breakpoint, number>;

type BreakpointValues = Record<Breakpoint, number>;

interface ResponsiveProps {
    className?: string;
    layouts: Layouts;
    cols: BreakpointCols;
    breakpoints: BreakpointValues;
    rowHeight: number;
    margin?: Margin;
    containerPadding?: Padding;
    draggableHandle?: string;
    isDraggable?: boolean;
    isResizable?: boolean;
    onLayoutChange?: (currentLayout: Layout[], allLayouts: Layouts) => void;
    onBreakpointChange?: (breakpoint: Breakpoint, cols: number) => void;
    children: React.ReactNode;
    width?: number;
}

interface DragState {
    id: string;
    originX: number;
    originY: number;
    startClientX: number;
    startClientY: number;
}

interface ResizeState {
    id: string;
    originW: number;
    originH: number;
    startClientX: number;
    startClientY: number;
}

const DEFAULT_MARGIN: Margin = [16, 16];
const DEFAULT_PADDING: Padding = [0, 0];

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const rectsOverlap = (a: LayoutItem, b: LayoutItem) => {
    if (a.i === b.i) {
        return false;
    }
    return (
        a.x < b.x + b.w &&
        a.x + a.w > b.x &&
        a.y < b.y + b.h &&
        a.y + a.h > b.y
    );
};

const resolveCollisions = (items: LayoutItem[], movingId: string): LayoutItem[] => {
    const adjusted = items.map((item) => ({ ...item }));
    const movingIndex = adjusted.findIndex((item) => item.i === movingId);
    if (movingIndex === -1) {
        return adjusted;
    }
    const moving = adjusted[movingIndex];

    let collisions = true;
    while (collisions) {
        collisions = false;
        for (const item of adjusted) {
            if (item.i === movingId) {
                continue;
            }
            if (rectsOverlap(moving, item)) {
                item.y = moving.y + moving.h;
                collisions = true;
            }
        }
    }

    return adjusted;
};

const sortedBreakpoints = (values: BreakpointValues) =>
    (Object.entries(values) as [Breakpoint, number][]).sort((a, b) => a[1] - b[1]);

const findBreakpoint = (width: number, values: BreakpointValues, fallback: Breakpoint): Breakpoint => {
    const sorted = sortedBreakpoints(values);
    let current: Breakpoint = fallback;
    for (const [key, value] of sorted) {
        if (width >= value) {
            current = key;
        }
    }
    return current;
};

const useStableCallback = <T extends (...args: any[]) => void>(callback?: T): T => {
    const ref = useRef<T | undefined>(callback);
    useEffect(() => {
        ref.current = callback;
    }, [callback]);
    return useCallback(((...args: Parameters<T>) => {
        ref.current?.(...args);
    }) as T, []);
};

const useLatestRef = <T,>(value: T) => {
    const ref = useRef(value);
    useEffect(() => {
        ref.current = value;
    }, [value]);
    return ref;
};

const getChildForKey = (children: React.ReactNode[], key: string) => {
    for (const child of children) {
        if (React.isValidElement(child) && child.key === key) {
            return child;
        }
    }
    return null;
};

const computePosition = (
    item: LayoutItem,
    cols: number,
    width: number,
    rowHeight: number,
    margin: Margin,
    padding: Padding,
) => {
    const [marginX, marginY] = margin;
    const [paddingX, paddingY] = padding;
    const effectiveWidth = Math.max(width - paddingX * 2, 0);
    const colWidth = cols > 0 ? (effectiveWidth - marginX * (cols - 1)) / cols : width;
    const unitX = colWidth + marginX;
    const unitY = rowHeight + marginY;
    const itemWidth = colWidth * item.w + marginX * Math.max(item.w - 1, 0);
    const itemHeight = rowHeight * item.h + marginY * Math.max(item.h - 1, 0);
    const left = paddingX + item.x * unitX;
    const top = paddingY + item.y * unitY;
    return { width: itemWidth, height: itemHeight, left, top };
};

const ResponsiveComponent: React.FC<ResponsiveProps> = ({
    className,
    layouts,
    cols,
    breakpoints,
    rowHeight,
    margin = DEFAULT_MARGIN,
    containerPadding = DEFAULT_PADDING,
    draggableHandle,
    isDraggable = true,
    isResizable = true,
    onLayoutChange,
    onBreakpointChange,
    children,
    width = 0,
}) => {
    const childrenArray = useMemo(() => React.Children.toArray(children), [children]);
    const layoutRef = useLatestRef(layouts);
    const colsRef = useLatestRef(cols);
    const breakpointsRef = useLatestRef(breakpoints);
    const dragState = useRef<DragState | null>(null);
    const resizeState = useRef<ResizeState | null>(null);
    const [activeBreakpoint, setActiveBreakpoint] = useState<Breakpoint>('lg');
    const containerRef = useRef<HTMLDivElement | null>(null);

    const emitLayoutChange = useStableCallback(onLayoutChange);
    const emitBreakpointChange = useStableCallback(onBreakpointChange);

    useEffect(() => {
        const bp = findBreakpoint(width, breakpointsRef.current, 'sm');
        setActiveBreakpoint((current) => {
            if (current !== bp) {
                emitBreakpointChange(bp, colsRef.current[bp]);
            }
            return bp;
        });
    }, [width, emitBreakpointChange, breakpointsRef, colsRef]);

    const currentLayout = useMemo(() => layoutRef.current[activeBreakpoint] || [], [layoutRef, activeBreakpoint]);
    const currentCols = colsRef.current[activeBreakpoint] || 1;

    const handlePointerMove = useCallback(
        (event: PointerEvent) => {
            const dragging = dragState.current;
            const resizing = resizeState.current;
            if (!dragging && !resizing) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();

            const layout = layoutRef.current[activeBreakpoint] || [];
            const currentColsCount = colsRef.current[activeBreakpoint] || 1;
            const container = containerRef.current;
            if (!container) {
                return;
            }
            const [marginX, marginY] = margin;
            const [paddingX, paddingY] = containerPadding;
            const effectiveWidth = Math.max(width - paddingX * 2, 0);
            const colWidth = currentColsCount > 0 ? (effectiveWidth - marginX * (currentColsCount - 1)) / currentColsCount : width;
            const unitX = colWidth + marginX;
            const unitY = rowHeight + marginY;

            if (dragging) {
                const target = layout.find((item) => item.i === dragging.id);
                if (!target || target.static) {
                    return;
                }
                const deltaX = event.clientX - dragging.startClientX;
                const deltaY = event.clientY - dragging.startClientY;
                const movedX = Math.round(deltaX / unitX);
                const movedY = Math.round(deltaY / unitY);
                const nextX = clamp(dragging.originX + movedX, 0, Math.max(currentColsCount - target.w, 0));
                const nextY = Math.max(dragging.originY + movedY, 0);
                if (nextX === target.x && nextY === target.y) {
                    return;
                }
                const updated = layout.map((item) =>
                    item.i === target.i
                        ? { ...item, x: nextX, y: nextY }
                        : { ...item },
                );
                const resolved = resolveCollisions(updated, target.i);
                const allLayouts = { ...layoutRef.current, [activeBreakpoint]: resolved };
                emitLayoutChange(resolved, allLayouts);
            } else if (resizing) {
                const target = layout.find((item) => item.i === resizing.id);
                if (!target || target.static) {
                    return;
                }
                const deltaX = event.clientX - resizing.startClientX;
                const deltaY = event.clientY - resizing.startClientY;
                const deltaCols = Math.round(deltaX / unitX);
                const deltaRows = Math.round(deltaY / unitY);
                const minW = target.minW ?? 1;
                const minH = target.minH ?? 1;
                const maxW = target.maxW ?? currentColsCount;
                const nextW = clamp(resizing.originW + deltaCols, minW, Math.min(maxW, currentColsCount - target.x));
                const nextH = Math.max(resizing.originH + deltaRows, minH);
                if (nextW === target.w && nextH === target.h) {
                    return;
                }
                const updated = layout.map((item) =>
                    item.i === target.i
                        ? { ...item, w: nextW, h: nextH }
                        : { ...item },
                );
                const resolved = resolveCollisions(updated, target.i);
                const allLayouts = { ...layoutRef.current, [activeBreakpoint]: resolved };
                emitLayoutChange(resolved, allLayouts);
            }
        },
        [activeBreakpoint, colsRef, emitLayoutChange, layoutRef, margin, containerPadding, rowHeight, width],
    );

    const endInteractions = useCallback(() => {
        dragState.current = null;
        resizeState.current = null;
        if (typeof window !== 'undefined') {
            window.removeEventListener('pointermove', handlePointerMove);
            window.removeEventListener('pointerup', endInteractions);
            window.removeEventListener('pointercancel', endInteractions);
        }
    }, [handlePointerMove]);

    const startDrag = useCallback(
        (id: string, event: React.PointerEvent<HTMLDivElement>) => {
            if (!isDraggable) {
                return;
            }
            if (draggableHandle) {
                const target = event.target as Element;
                if (!target.closest(draggableHandle)) {
                    return;
                }
            }
            event.preventDefault();
            event.stopPropagation();
            const layout = layoutRef.current[activeBreakpoint] || [];
            const item = layout.find((entry) => entry.i === id);
            if (!item || item.static) {
                return;
            }
            dragState.current = {
                id,
                originX: item.x,
                originY: item.y,
                startClientX: event.clientX,
                startClientY: event.clientY,
            };
            if (typeof window !== 'undefined') {
                window.addEventListener('pointermove', handlePointerMove);
                window.addEventListener('pointerup', endInteractions, { once: true });
                window.addEventListener('pointercancel', endInteractions, { once: true });
            }
        },
        [activeBreakpoint, draggableHandle, endInteractions, handlePointerMove, isDraggable, layoutRef],
    );

    const startResize = useCallback(
        (id: string, event: React.PointerEvent<HTMLDivElement>) => {
            if (!isResizable) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            const layout = layoutRef.current[activeBreakpoint] || [];
            const item = layout.find((entry) => entry.i === id);
            if (!item || item.static) {
                return;
            }
            resizeState.current = {
                id,
                originW: item.w,
                originH: item.h,
                startClientX: event.clientX,
                startClientY: event.clientY,
            };
            if (typeof window !== 'undefined') {
                window.addEventListener('pointermove', handlePointerMove);
                window.addEventListener('pointerup', endInteractions, { once: true });
                window.addEventListener('pointercancel', endInteractions, { once: true });
            }
        },
        [activeBreakpoint, endInteractions, handlePointerMove, isResizable, layoutRef],
    );

    useEffect(() => {
        return () => {
            if (typeof window !== 'undefined') {
                window.removeEventListener('pointermove', handlePointerMove);
                window.removeEventListener('pointerup', endInteractions);
                window.removeEventListener('pointercancel', endInteractions);
            }
        };
    }, [handlePointerMove, endInteractions]);

    const positionedChildren = useMemo(() => {
        return currentLayout.map((item) => {
            const child = getChildForKey(childrenArray, item.i);
            if (!child) {
                return null;
            }
            const { width: itemWidth, height: itemHeight, left, top } = computePosition(
                item,
                currentCols,
                width,
                rowHeight,
                margin,
                containerPadding,
            );
            return (
                <div
                    key={item.i}
                    className="rgl-item"
                    style={{
                        position: 'absolute',
                        left,
                        top,
                        width: itemWidth,
                        height: itemHeight,
                        transition: dragState.current || resizeState.current ? 'none' : 'transform 150ms ease, width 150ms ease, height 150ms ease',
                    }}
                    onPointerDown={(event) => startDrag(item.i, event)}
                >
                    {child}
                    {isResizable && !item.static && (
                        <div
                            className="rgl-resize-handle"
                            onPointerDown={(event) => startResize(item.i, event)}
                            style={{
                                position: 'absolute',
                                right: 4,
                                bottom: 4,
                                width: 12,
                                height: 12,
                                cursor: 'nwse-resize',
                                background: 'transparent',
                                touchAction: 'none',
                            }}
                        />
                    )}
                </div>
            );
        });
    }, [
        childrenArray,
        containerPadding,
        currentCols,
        currentLayout,
        isResizable,
        margin,
        rowHeight,
        startDrag,
        startResize,
        width,
    ]);

    const totalHeight = useMemo(() => {
        if (currentLayout.length === 0) {
            return 0;
        }
        const maxItem = currentLayout.reduce((acc, item) => {
            const bottom = item.y + item.h;
            return bottom > acc ? bottom : acc;
        }, 0);
        const [marginX, marginY] = margin;
        const [paddingX, paddingY] = containerPadding;
        return (
            paddingY * 2 +
            maxItem * rowHeight +
            Math.max(maxItem - 1, 0) * marginY
        );
    }, [containerPadding, currentLayout, margin, rowHeight]);

    return (
        <div ref={containerRef} className={className} style={{ position: 'relative', width: '100%', height: totalHeight }}>
            {positionedChildren}
        </div>
    );
};

export const Responsive = ResponsiveComponent;

export function WidthProvider<T extends React.ComponentType<any>>(Component: T) {
    const WidthProviderComponent: React.FC<React.ComponentProps<T>> = (props) => {
        const [width, setWidth] = useState(0);
        const containerRef = useRef<HTMLDivElement | null>(null);

        useEffect(() => {
            const element = containerRef.current;
            if (!element) {
                return;
            }
            if (typeof ResizeObserver === 'undefined') {
                setWidth(element.getBoundingClientRect().width);
                return;
            }
            const observer = new ResizeObserver((entries) => {
                for (const entry of entries) {
                    setWidth(entry.contentRect.width);
                }
            });
            observer.observe(element);
            setWidth(element.getBoundingClientRect().width);
            return () => observer.disconnect();
        }, []);

        return (
            <div ref={containerRef} style={{ width: '100%' }}>
                <Component {...(props as React.ComponentProps<T>)} width={width} />
            </div>
        );
    };

    WidthProviderComponent.displayName = `WidthProvider(${Component.displayName || Component.name || 'Component'})`;

    return WidthProviderComponent as unknown as T;
}

export default ResponsiveComponent;
