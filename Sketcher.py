import cv2

class Sketcher:
    def __init__(self, measureUnit, measureName):
        '''
        {Number} measureUnit - Amount of pixels in one distance unit
        {String} measureName - The name of the measure unit
        '''

        self.measure_unit = measureUnit
        self.measure_name = measureName

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