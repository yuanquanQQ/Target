import cv2
import numpy as np

class Sketcher:
    def __init__(self, measureUnit, measureName):
        '''
        {Number} measureUnit - Amount of pixels in one distance unit
        {String} measureName - The name of the measure unit
        '''

        self.measure_unit = measureUnit
        self.measure_name = measureName
        
        # 添加靶环颜色定义
        self.target_colors = [
            (255, 255, 255),  # 白色 - 1环
            (255, 255, 255),  # 白色 - 2环
            (0, 0, 0),        # 黑色 - 3环
            (0, 0, 0),        # 黑色 - 4环
            (66, 66, 231),    # 蓝色 - 5环
            (66, 66, 231),    # 蓝色 - 6环
            (0, 0, 204),      # 红色 - 7环
            (0, 0, 204),      # 红色 - 8环
            (0, 204, 255),    # 黄色 - 9环
            (0, 204, 255),    # 黄色 - 10环
        ]

    def draw_data_block(self, img):
        '''
        Draw the rectangle on which the data of the analysis is written.

        Parameters:
            {Numpy.array} img - The img on which to draw
        '''

        img_h, img_w, _ = img.shape
        
        rect_0_start = (int(img_w * .5), int(img_h * .85))
        rect_0_end = (img_w, img_h)
        cv2.rectangle(img, rect_0_start, rect_0_end, (0xff,0xff,0xff), -1)
        
        rect_1_start = (rect_0_start[0] - 60, int(img_h * .85))
        rect_1_end = (rect_0_start[0] - 15, img_h)
        cv2.rectangle(img, rect_1_start, rect_1_end, (0x28,0x28,0x28), -1)
        
        rect_2_start = (rect_1_start[0] - 50, int(img_h * .85))
        rect_2_end = (rect_1_start[0] - 15, img_h)
        cv2.rectangle(img, rect_2_start, rect_2_end, (248,138,8), -1)
        
        rect_3_start = (rect_2_start[0] - 40, int(img_h * .85))
        rect_3_end = (rect_2_start[0] - 15, img_h)
        cv2.rectangle(img, rect_3_start, rect_3_end, (66,0x0,0xff), -1)
        
        rect_4_start = (rect_3_start[0] - 30, int(img_h * .85))
        rect_4_end = (rect_3_start[0] - 15, img_h)
        cv2.rectangle(img, rect_4_start, rect_4_end, (0x0,204,0xff), -1)
        
        rect_5_start = (rect_4_start[0] - 20, int(img_h * .85))
        rect_5_end = (rect_4_start[0] - 15, img_h)
        cv2.rectangle(img, rect_5_start, rect_5_end, (0x0,204,0xff), -1)

    def draw_target_simulation(self, img, hits, target_center=None, target_radius=None):
        '''
        在视频右上角绘制模拟靶面展示
        
        Parameters:
            {Numpy.array} img - 要绘制的图像
            {List} hits - 命中点列表
            {Tuple} target_center - 靶心坐标，如果为None则自动计算
            {Number} target_radius - 靶半径，如果为None则自动计算
        '''
        img_h, img_w, _ = img.shape
        
        # 设置模拟靶的大小和位置
        sim_size = min(img_w // 4, img_h // 4)  # 模拟靶的大小
        sim_margin = 20  # 边距
        
        # 创建一个白色背景的模拟靶区域
        sim_target = np.ones((sim_size, sim_size, 3), dtype=np.uint8) * 255
        
        # 计算模拟靶的中心点
        sim_center = (sim_size // 2, sim_size // 2)
        
        # 计算每个环的半径 (10环到1环)
        ring_step = sim_size // 22  # 每环宽度
        ring_radii = [(i + 1) * ring_step for i in range(10)]
        ring_radii.reverse()  # 从外到内排列
        
        # 绘制靶环 (从外到内)
        for i, radius in enumerate(ring_radii):
            color = self.target_colors[i]
            cv2.circle(sim_target, sim_center, radius, color, -1)
        
        # 绘制靶心
        cv2.circle(sim_target, sim_center, ring_radii[9] // 2, (0, 204, 255), -1)
        
        # 如果有命中点，则在模拟靶上标记
        if hits and target_center and target_radius:
            # 计算缩放比例
            scale_factor = sim_size / (target_radius * 2.2)
            
            for hit in hits:
                # 计算命中点相对于靶心的偏移
                dx = hit.point[0] - target_center[0]
                dy = hit.point[1] - target_center[1]
                
                # 缩放偏移量
                scaled_dx = int(dx * scale_factor)
                scaled_dy = int(dy * scale_factor)
                
                # 计算在模拟靶上的坐标
                sim_x = sim_center[0] + scaled_dx
                sim_y = sim_center[1] + scaled_dy
                
                # 确保坐标在模拟靶范围内
                sim_x = max(0, min(sim_x, sim_size - 1))
                sim_y = max(0, min(sim_y, sim_size - 1))
                
                # 绘制命中点
                cv2.circle(sim_target, (sim_x, sim_y), 5, (0, 0, 0), 2)
                cv2.circle(sim_target, (sim_x, sim_y), 3, (0, 0, 255), -1)
                
                # 显示环数
                if hit.score > 0:
                    cv2.putText(sim_target, str(hit.score), (sim_x + 8, sim_y), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                    cv2.putText(sim_target, str(hit.score), (sim_x + 8, sim_y), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 在原图右上角放置模拟靶
        x_offset = img_w - sim_size - sim_margin
        y_offset = sim_margin
        
        # 创建一个半透明的背景
        overlay = img.copy()
        cv2.rectangle(overlay, (x_offset - 10, y_offset - 10), 
                     (x_offset + sim_size + 10, y_offset + sim_size + 10), 
                     (255, 255, 255), -1)
        
        # 应用半透明效果
        alpha = 0.8
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        
        # 将模拟靶放置到原图上
        img[y_offset:y_offset+sim_size, x_offset:x_offset+sim_size] = sim_target
        
        # 添加边框
        cv2.rectangle(img, (x_offset - 10, y_offset - 10), 
                     (x_offset + sim_size + 10, y_offset + sim_size + 10), 
                     (0, 0, 0), 2)
        
        # 添加标题
        cv2.putText(img, "靶面模拟", (x_offset, y_offset - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    def mark_hits(self, img, hits, foreground, diam, withOutline, withScore):
        '''
        Mark hits on the target itself.

        Parameters:
            {Numpy.array} img - The img on which to draw
            {List} hits - [
                             {HitsManager.Hit} A hit on the target
                             ...
                          ]
            {Tuple} foreground - The color of the cirle [BGR]
            {Number} diam - The circle's diameter
            {Boolean} withOutline - True to add an outline to the circle
            {Boolean} withScore - True to add a score notation on top of the circle
        '''

        outline = (0x0,0x0,0x0)
        
        for hit in hits:
            x, y = hit.point[0], hit.point[1]
            score_string = str(hit.score) if (hit.score > 0) else 'miss'
            
            if withOutline:
                cv2.circle(img, (x,y), 10, outline, diam + 2)
                
            cv2.circle(img, (x,y), 8, foreground, diam)
            
            if withScore:
                cv2.putText(img, score_string, (x,y - 20), cv2.FONT_HERSHEY_PLAIN, 2, outline, thickness=2)
                cv2.putText(img, score_string, (x,y - 20), cv2.FONT_HERSHEY_PLAIN, 2, (0xff,0xff,0xff), thickness=2)
        
        # 在这里调用模拟靶面绘制函数
        # 注意：需要从外部传入靶心坐标和靶半径
        # 这里假设靶心和半径可以从其他地方获取
        # 如果没有这些信息，可以在Driver.py中修改调用方式
        if hits:
            # 这里需要从外部获取靶心和半径
            # 暂时使用None，实际使用时需要替换为真实值
            target_center = getattr(self, 'target_center', None)
            target_radius = getattr(self, 'target_radius', None)
            self.draw_target_simulation(img, hits, target_center, target_radius)

    def draw_grouping(self, img, contour):
        '''
        Mark hits on the target itself.

        Parameters:
            {Numpy.array} img - The img on which to draw
            {Numpy.array} contour - The external contour of the group
        '''

        cv2.drawContours(img, contour, -1, (214,215,97), 2)

    def type_arrows_amount(self, img, amount, dataColor):
        '''
        Write the 'Arrows shot' segment, referencing the amount of arrows on the target.

        Parameters:
            {Numpy.array} img - The img on which to draw
            {Number} amount - The amount of arrows currently on the target
            {Tuple} dataColor - The color of the value text [BGR]
        '''

        amount = str(amount)
        img_h, img_w, _ = img.shape
        cv2.putText(img, 'Arrows shot: ', (int(img_w * .52), int(img_h * .905)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0x0,0x0,0x0), 1)
        
        cv2.putText(img, amount, (int(img_w * .675), int(img_h * .905)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, dataColor, 1)

    def type_grouping_diameter(self, img, diameter, dataColor):
        '''
        Write the 'Grouping' segment, referencing the diameter of the grouping contour.

        Parameters:
            {Numpy.array} img - The img on which to draw
            {Number} diameter - The diameter of the grouping
            {Tuple} dataColor - The color of the value text [BGR]
        '''

        diameter = str(round(diameter * self.measure_unit, 1))
        img_h, img_w, _ = img.shape
        cv2.putText(img, 'Grouping: ', (int(img_w * .77), int(img_h * .905)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0x0,0x0,0x0), thickness=1)
        
        cv2.putText(img, diameter + self.measure_name, (int(img_w * .89), int(img_h * .905)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, dataColor, 1)

    def type_total_score(self, img, totalScore, achievableScore, dataColor):
        '''
        Write the 'Grouping' segment, referencing the diameter of the grouping contour.

        Parameters:
            {Numpy.array} img - The img on which to draw
            {Number} totalScore - The total calculated score
            {Number} achievableScore - The maximum score that could have been achieved with
                                       the current amount of arrows on the target
            {Tuple} dataColor - The color of the value text [BGR]
        '''

        totalScore = str(totalScore)
        achievableScore = str(achievableScore)
        score_digits = len(totalScore)
        score_space = 23 * (score_digits - 1)
        img_h, img_w, _ = img.shape
        
        cv2.putText(img, 'Total score: ', (int(img_w * .52), int(img_h * .975)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0x0,0x0,0x0), thickness=1)
        
        cv2.putText(img, totalScore, (int(img_w * .67), int(img_h * .975)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, dataColor, 1)
        
        cv2.putText(img, '/ ' + achievableScore, (int(img_w * .695 + score_space), int(img_h * .975)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0x0,0x0,0x0), 1)