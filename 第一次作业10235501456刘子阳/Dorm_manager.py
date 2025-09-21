class DormitoryManager:
    def __init__(self):
        self.students = {}  # 存储学生信息，学号为键
        self.init_sample_data()

    def init_sample_data(self):
        sample_students = [
            {"学号": "2024001", "姓名": "张三", "性别": "男", "宿舍房间号": "A101", "联系电话": "13800138001"},
            {"学号": "2024002", "姓名": "李四", "性别": "女", "宿舍房间号": "B202", "联系电话": "13800138002"},
            {"学号": "2024003", "姓名": "王五", "性别": "男", "宿舍房间号": "A101", "联系电话": "13800138003"},
            {"学号": "2024004", "姓名": "刘洋", "性别": "女", "宿舍房间号": "B202", "联系电话": "13800138004"},
            {"学号": "2024005", "姓名": "罗琦", "性别": "女", "宿舍房间号": "B202", "联系电话": "13800138005"},
            {"学号": "2024006", "姓名": "赵凯", "性别": "男", "宿舍房间号": "A202", "联系电话": "13800138006"}
        ]

        for student in sample_students:
            self.students[student["学号"]] = student

    def count_room_students(self, room_number):
        count = 0
        for student in self.students.values():
            if student["宿舍房间号"] == room_number:
                count += 1
        return count

    def search_student_by_id(self):
        print("\n=== 按学号查询学生信息 ===")
        student_id = input("请输入学号: ").strip()

        if not student_id:
            print("学号不能为空！")
            return

        if student_id in self.students:
            student = self.students[student_id]
            print("\n学生信息如下：")
            print("-" * 30)
            print(f"学号: {student['学号']}")
            print(f"姓名: {student['姓名']}")
            print(f"性别: {student['性别']}")
            print(f"宿舍房间号: {student['宿舍房间号']}")
            print(f"联系电话: {student['联系电话']}")
            print("-" * 30)
        else:
            print(f"未找到学号为 {student_id} 的学生！")

    def add_new_student(self):
        print("\n=== 录入新的学生信息 ===")

        # 输入学号
        student_id = input("请输入学号: ").strip()
        if not student_id:
            print("学号不能为空！")
            return

        if student_id in self.students:
            print(f"学号 {student_id} 已存在！")
            return

        # 输入姓名
        name = input("请输入姓名: ").strip()
        if not name:
            print("姓名不能为空！")
            return

        # 输入性别
        while True:
            gender = input("请输入性别(男/女): ").strip()
            if gender in ['男', '女']:
                break
            else:
                print("性别只能输入'男'或'女'！")

        # 输入宿舍房间号并检查人数限制
        while True:
            room_number = input("请输入宿舍房间号: ").strip()
            if not room_number:
                print("宿舍房间号不能为空！")
                continue

            current_count = self.count_room_students(room_number)
            if current_count >= 4:
                print(f"宿舍 {room_number} 已满员（4人），请选择其他宿舍！")
                continue
            else:
                print(f"宿舍 {room_number} 当前有 {current_count} 人，可以入住。")
                break

        # 输入联系电话
        while True:
            phone = input("请输入联系电话: ").strip()
            if phone.isdigit() and len(phone) == 11:
                break
            else:
                print("请输入有效的手机号码（11位数字）！")

        # 保存学生信息
        student_info = {
            "学号": student_id,
            "姓名": name,
            "性别": gender,
            "宿舍房间号": room_number,
            "联系电话": phone
        }

        self.students[student_id] = student_info
        print(f"\n学生 {name} 的信息录入成功！")
        print(f"宿舍 {room_number} 现在有 {current_count + 1} 人。")

    def display_all_students(self):
        print("\n=== 所有学生信息 ===")

        if not self.students:
            print("系统中暂无学生信息！")
            return

        print(f"共有 {len(self.students)} 名学生：")
        print("-" * 70)
        print(f"{'学号':<10} {'姓名':<8} {'性别':<4} {'宿舍房间号':<10} {'联系电话':<12}")
        print("-" * 70)

        # 按学号排序显示
        sorted_students = sorted(self.students.items())
        for student_id, student_info in sorted_students:
            print(f"{student_info['学号']:<10} {student_info['姓名']:<8} "
                  f"{student_info['性别']:<4} {student_info['宿舍房间号']:<10} "
                  f"{student_info['联系电话']:<12}")

        print("-" * 70)

        # 宿舍人数统计
        room_count = {}
        for student in self.students.values():
            room = student['宿舍房间号']
            room_count[room] = room_count.get(room, 0) + 1

        print("\n各宿舍人数统计：")
        for room, count in sorted(room_count.items()):
            print(f"宿舍 {room}: {count} 人")

def main():
    manager = DormitoryManager()

    # 功能菜单
    print("=" * 50)
    print("学生宿舍管理程序")
    print("=" * 50)
    print("可以提供3个功能：")
    print("1. 按学号查询某一位学生的具体信息")
    print("2. 录入新的学生信息")
    print("3. 显示现有的所有学生的信息")
    print("0. 退出程序")
    print("=" * 50)

    while True:
        try:
            print("\n" + "-" * 40)
            choice = input("请输入功能编号 (1/2/3，输入0退出): ").strip()

            if choice == '1':
                manager.search_student_by_id()
            elif choice == '2':
                manager.add_new_student()
            elif choice == '3':
                manager.display_all_students()
            elif choice == '0':
                print("程序结束，再见！")
                break
            else:
                print("请输入有效的选项：1、2、3或0！")

        except KeyboardInterrupt:
            print("\n程序被用户中断，正在退出...")
            break
        except Exception as e:
            print(f"程序运行出现错误: {e}")


if __name__ == "__main__":
    main()