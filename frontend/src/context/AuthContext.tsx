import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

// Định nghĩa interface cho Context để kiểm soát kiểu dữ liệu
interface AuthContextType {
  user: string | null;                       // Tên người dùng hoặc null nếu chưa đăng nhập
  setUser: (user: string | null) => void;   // Hàm để cập nhật thông tin người dùng
}

// Tạo Context để chia sẻ trạng thái người dùng trong toàn bộ ứng dụng
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// AuthProvider: Bao bọc các component con và cung cấp context
export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  // Khởi tạo state `user` từ localStorage (nếu đã lưu từ trước)
  const [user, setUser] = useState<string | null>(localStorage.getItem("userName"));

  useEffect(() => {
    // Hàm kiểm tra trạng thái xác thực người dùng
    const checkAuth = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        // Nếu không có token => người dùng chưa đăng nhập
        setUser(null);
        return;
      }

      try {
        // Gửi request để kiểm tra token hợp lệ và lấy thông tin người dùng
        const response = await axios.get("http://localhost:5000/api/v1/auth/me", {
          headers: { Authorization: `Bearer ${token}` }, // Đính kèm token vào header
        });
        // Nếu hợp lệ, cập nhật tên người dùng từ response
        setUser(response.data.name);
      } catch {
        // Nếu lỗi (token hết hạn hoặc không hợp lệ) => đăng xuất người dùng
        setUser(null);
        localStorage.removeItem("token");
        localStorage.removeItem("userName");
      }
    };

    // Gọi hàm kiểm tra khi component được mount
    checkAuth();
  }, []);

  // Truyền giá trị context gồm user và setUser xuống các component con
  return <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>;
};

// Custom hook giúp truy cập AuthContext một cách tiện lợi
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
