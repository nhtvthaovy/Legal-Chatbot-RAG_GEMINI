import { useNavigate, Link } from "react-router-dom";
import { Bot, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext"; // Import AuthContext

const NavBar = () => {
  const { user, setUser } = useAuth(); // Lấy thông tin user từ context
  const navigate = useNavigate();


  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userName");
    setUser(null); // Cập nhật context khi đăng xuất
    navigate("/");
  };

  return (
    <header className="relative bg-transparent text-[rgb(72,56,56)] shadow-lg backdrop-blur-xl py-6 border-2 border-pink-300 rounded-2xl mb-2">
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.2)_0%,rgba(255,255,255,0)_100%)]"></div>
      <div className="container mx-auto px-4 flex items-center justify-between relative z-10">
        
        {/* Logo */}
        <button
          onClick={() => navigate("/")} // Điều hướng về trang chủ
          className="group flex items-center gap-3 transform-gpu transition-all duration-300 hover:scale-105"
        >
          <div className="relative">
            <div className="absolute inset-0 bg-[#20C997] rounded-xl rotate-[-10deg] blur-[10px] opacity-70 group-hover:rotate-[10deg] group-hover:scale-110 transition-all duration-300"></div>
            <div className="relative from-[#20C997] to-[#96F2D7] p-2 rounded-xl transform rotate-[-10deg] group-hover:rotate-[10deg] transition-all duration-300 shadow-[5px_5px_15px_rgba(0,0,0,0.2)]">
              <Bot className="h-8 w-8 text-white" />
            </div>
          </div>
        </button>

        {/* Navigation Menu */}
        <nav className="flex space-x-6 mx-auto text-sm md:text-lg">
          {["Trang Chủ", "ChatBot", "Pháp Điển"].map((item) =>
            item === "Pháp Điển" ? (
              <a
                key={item}
                href="/phapdien/BoPhapDien.html"
                className="relative px-2 py-1 font-bold hover:text-[#20C997]"
              >
                {item}
              </a>
            ) : (
              <Link
                key={item}
                to={item === "Trang Chủ" ? "/" : "/chat"}
                className="relative px-2 py-1 font-bold hover:text-[#20C997]"
              >
                {item}
              </Link>
            )
          )}
        </nav>

        {/* Auth Links */}
        <div className="flex space-x-2 text-sm md:text-base">
          {user ? (
            <div className="flex items-center space-x-4">
              <span className="font-semibold">Xin chào, {user}</span>
              <button onClick={handleLogout} className="px-3 py-1 rounded-md hover:bg-white/20">
                <LogOut className="w-5 h-5 text-red-500" />
              </button>
            </div>
          ) : (
            <Link to="/login" className="px-3 py-1 rounded-md font-semibold hover:bg-white/20">
              Đăng nhập
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default NavBar;
