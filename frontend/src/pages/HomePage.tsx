import { Link } from "react-router-dom";
import { Bot } from "lucide-react";
import Footer from "../components/Footer";

const HomePage = () => {
  return (
    <div className="flex flex-col min-h-screen bg-[#FFF9F4] overflow-hidden">

      <main className="flex-grow">
        {/* Hero Section */}
        <section className="relative h-[80vh] overflow-hidden flex items-center">
          {/* Hiệu ứng nền */}
          <div className="absolute inset-0">
            {[...Array(27)].map((_, i) => (
              <div
                key={i}
                className="absolute rounded-full mix-blend-multiply animate-float"
                style={{
                  width: `${Math.random() * 100 + 50}px`,
                  height: `${Math.random() * 100 + 50}px`,
                  backgroundColor: `hsl(${Math.random() * 360}, 70%, 85%)`,
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animation: `float ${
                    Math.random() * 1 + 5
                  }s infinite ease-in-out`,
                }}
              ></div>
            ))}
          </div>
          <div className="absolute inset-0 bg-gradient-to-b from-[#F3F9FF] to-[#F1F9F5] opacity-10"></div>

          {/* Nội dung chính */}
          <div className="container mx-auto px-4 relative z-10 flex flex-col items-center text-center">
            {/* Tiêu đề */}
            <h1 className="relative text-5xl md:text-6xl font-extrabold tracking-wide text-black mb-6">
  <span className="relative z-10">Khám Phá</span>
  <span className="absolute inset-x-0 bottom-0 h-1 bg-orange-400 rounded-full"></span>
</h1>



            <h2 className="relative inline-block px-8 py-5 bg-[#FF9F45] text-white rounded-lg font-black text-5xl uppercase tracking-wide shadow-xl mb-10">
              ChatBot Pháp Luật Việt Nam
              <span className="absolute inset-x-0 inset-y-0 bg-[#FF6F00] -z-10 translate-x-3 translate-y-3 rounded-lg opacity-90"></span>
              <span className="absolute inset-x-1 inset-y-1 bg-[#FFC69B] -z-20 translate-x-5 translate-y-5 rounded-lg opacity-80"></span>
            </h2>

            {/* Nút */}
            <style>
              {`
              @keyframes bounce {
                0%, 100% {
                  transform: translateY(0);
                }
                50% {
                  transform: translateY(-8px);
                }
              }
              `}
            </style>

            <Link
              to="/chat"
              className="inline-flex items-center gap-2 bg-[#F8AFA6] text-white px-10 py-5 rounded-full text-lg font-bold 
                shadow-[0_6px_0px_#D98B81,0_10px_20px_rgba(0,0,0,0.2)] 
                animate-[bounce_1.5s_infinite]"
            >
              <Bot className="h-6 w-6 text-white" />
            </Link>
          </div>
        </section>

        <Footer />
      </main>
    </div>
  );
};

export default HomePage;
