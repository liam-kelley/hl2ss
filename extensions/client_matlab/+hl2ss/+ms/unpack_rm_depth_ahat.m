
function data = unpack_rm_depth_ahat(response, mode)
if (response.status == 0)
    if (mode == hl2ss.stream_mode.MODE_1)
        pose = response.pose; 
    else
        pose = zeros([4, 4], 'single');
    end

    data = struct('frame_index',  response.frame_index,  ...
                  'status',       response.status,       ...
                  'timestamp',    response.timestamp,    ...
                  'depth',        response.depth,        ...
                  'ab',           response.ab,           ...
                  'sensor_ticks', response.sensor_ticks, ...
                  'pose',         pose);
else
    image_size = [hl2ss.parameters_rm_depth_ahat.HEIGHT, hl2ss.parameters_rm_depth_ahat.WIDTH];
    zero_image = zeros(image_size, 'uint16');
    
    data = struct('frame_index',  response.frame_index,    ...
                  'status',       response.status,         ...
                  'timestamp',    zeros([1, 1], 'uint64'), ...
                  'depth',        zero_image,              ...
                  'ab',           zero_image,              ...
                  'sensor_ticks', zeros([1, 1], 'uint64'), ...
                  'pose',         zeros([4, 4], 'single'));
end
end
