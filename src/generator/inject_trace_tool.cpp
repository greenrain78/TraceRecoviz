// inject_trace_tool.cpp
#include <string>
#include <sstream>
#include <vector>
#include <set>
#include <iostream>
#include "clang/AST/AST.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/AST/DeclCXX.h"
#include "clang/AST/Decl.h"
#include "clang/AST/Type.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Stmt.h"
//#include "clang/AST/DynTypedNodeList.h"
#include "clang/AST/ParentMapContext.h"
#include "clang/AST/ParentMap.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Lex/Lexer.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Frontend/ASTConsumers.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Tooling/CommonOptionsParser.h"
//#include "clang/Tooling/FixedCompilationDatabase.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/ADT/SmallString.h"


using namespace clang;
using namespace clang::tooling;

// 함수 내 ReturnStmt 탐색용 방문자
class ReturnVisitor : public RecursiveASTVisitor<ReturnVisitor> {
public:
    explicit ReturnVisitor(std::vector<ReturnStmt*>& R) : returns(R) {}
    bool VisitReturnStmt(ReturnStmt* ret) {
        returns.push_back(ret);
        return true;
    }
private:
    std::vector<ReturnStmt*>& returns;
};

// ASTVisitor: 함수 정의마다 처리
class TraceInjectorVisitor : public RecursiveASTVisitor<TraceInjectorVisitor> {
public:
explicit TraceInjectorVisitor(Rewriter &R, ASTContext &C) : TheRewriter(R), Context(C) {}
    bool VisitFunctionDecl(FunctionDecl *f) {
        // Objective-C 코드 무조건 건너뛰기 (안 쓰니까)
        if (isa<ObjCMethodDecl>(f) ||!f->hasBody() || f->isImplicit() || f->isDeleted())
            return true;

        // 시스템 헤더는 여전히 제외, BUT 프로젝트 헤더는 포함
        if (TheRewriter.getSourceMgr().isInSystemHeader(f->getLocation()))
            return true;
        // if (TheRewriter.getSourceMgr().isInSystemHeader(f->getLocation()) &&
        //     !TheRewriter.getSourceMgr().isInMainFile(f->getLocation()))
        //     return true;


        // 테스트 프레임워크 내부 함수 스킵 (네임스페이스 testing 등)
        if (f->getQualifiedNameAsString().rfind("testing::", 0) == 0)
            return true;

        //std::string funcKey = f->getQualifiedNameAsString();
        std::string fileName = TheRewriter.getSourceMgr().getFilename(f->getLocation()).str();
        std::string funcKey = f->getQualifiedNameAsString() + "@" + fileName;

        if (VisitedFunctions.find(funcKey) != VisitedFunctions.end()) {
            return true;
        }
        VisitedFunctions.insert(funcKey);
        // 함수 몸체(CompoundStmt) 가져오기
        CompoundStmt* body = dyn_cast<CompoundStmt>(f->getBody());
        if (!body) return true;

        // 반환형과 함수 이름 등 문자열 생성
        std::string className;
        bool isMethod = false;
        if (CXXMethodDecl *md = dyn_cast<CXXMethodDecl>(f)) {
            isMethod = true;
            if (md->getParent()) {
                if (const ClassTemplateSpecializationDecl* spec =
                    dyn_cast<ClassTemplateSpecializationDecl>(md->getParent())) {
                    const TemplateArgumentList& args = spec->getTemplateArgs();
                    std::string templateArgsStr = "<";
                    for (unsigned i = 0; i < args.size(); ++i) {
                        if (i > 0) templateArgsStr += ", ";
                        const TemplateArgument& arg = args.get(i);
                        switch (arg.getKind()) {
                            case TemplateArgument::Type: {
                                QualType qt = arg.getAsType();
                                QualType canonical = qt.getCanonicalType();  // 💡 canonical type로 풀기
                                templateArgsStr += canonical.getAsString();
                                break;
                            }
                            case TemplateArgument::Integral: {
                                llvm::APSInt val = arg.getAsIntegral();
                                llvm::SmallString<16> s;
                                val.toString(s, 10);
                                templateArgsStr += s.c_str();
                                break;
                            }
                            default:
                                templateArgsStr += "<unknown>";
                                break;
                        }
                    }
                    templateArgsStr += ">";
                    className = spec->getNameAsString() + templateArgsStr;
                } else {
                    className = md->getParent()->getNameAsString();
                }
            }
        }
        std::string funcName;
        if (const FunctionTemplateSpecializationInfo* funcSpecInfo = f->getTemplateSpecializationInfo()) {
            const TemplateArgumentList* args = funcSpecInfo->TemplateArguments;
            if (args) {
                std::string templateArgsStr = "<";
                for (unsigned i = 0; i < args->size(); ++i) {
                    if (i > 0) templateArgsStr += ", ";
                    const TemplateArgument& arg = args->get(i);
                    switch (arg.getKind()) {
                        case TemplateArgument::Type: {
                            QualType qt = arg.getAsType();
                            QualType canonical = qt.getCanonicalType();
                            templateArgsStr += canonical.getAsString();
                            break;
                        }
                        
                        
                        case TemplateArgument::Integral: {
                            llvm::APSInt val = arg.getAsIntegral();
                            llvm::SmallString<16> s;
                            val.toString(s, 10);
                            templateArgsStr += s.c_str();
                            break;
                        }
                        case TemplateArgument::Declaration:
                            templateArgsStr += "<decl>";
                            break;
                        case TemplateArgument::NullPtr:
                            templateArgsStr += "nullptr";
                            break;
                        case TemplateArgument::Template:
                            templateArgsStr += arg.getAsTemplate().getAsTemplateDecl()->getNameAsString();
                            break;
                        case TemplateArgument::TemplateExpansion:
                            templateArgsStr += "<template-expansion>";
                            break;
                        case TemplateArgument::Expression:
                            templateArgsStr += "<expr>";
                            break;
                        default:
                            templateArgsStr += "<unknown>";
                            break;
                    }
                }
                templateArgsStr += ">";
                funcName = f->getNameAsString() + templateArgsStr;
            }
        }
        

        if (funcName.empty()) {
            funcName = f->getQualifiedNameAsString();
        }

        if (!className.empty() && funcName.find(className) != std::string::npos) {
            size_t pos = funcName.find(className);
            funcName.replace(pos, className.length(), className);
        }

        // 생성자인 경우, 반환형으로 클래스명 사용
        QualType retTypeQual = f->getReturnType();
        std::string retTypeStr = retTypeQual.getAsString();
        if (CXXConstructorDecl *cd = dyn_cast<CXXConstructorDecl>(f)) {
            // 생성자: 반환형을 클래스명으로 대체
            retTypeStr = cd->getParent()->getNameAsString();
        } else if (CXXDestructorDecl *dd = dyn_cast<CXXDestructorDecl>(f)) {
            // 소멸자: 반환형 void로 처리
            retTypeStr = "void";
        }
        
        // 매개변수 타입 목록
        std::string params;
        for (unsigned i = 0; i < f->getNumParams(); ++i) {
            if (i) params += ",";
            QualType qt = f->getParamDecl(i)->getType();
            params += qt.getAsString();
        }


        std::string fullFuncName;
        if (!className.empty()) {
            fullFuncName = className + "::" + f->getNameAsString();
        } else {
            fullFuncName = f->getQualifiedNameAsString();
        }

        std::string signature = retTypeStr + " " + fullFuncName + "(" + params + ")";

        // [1] 함수 시작 부분에 trace_enter 삽입
        // 객체 포인터 표현: 멤버함수인지 확인
        std::string objExpr = "(void*)0";
        if (CXXMethodDecl *md = dyn_cast<CXXMethodDecl>(f)) {
            if (!md->isStatic() &&
                !(md->isOverloadedOperator() &&
                (md->getOverloadedOperator() == OO_New || md->getOverloadedOperator() == OO_Delete ||
                md->getOverloadedOperator() == OO_Array_New || md->getOverloadedOperator() == OO_Array_Delete))) {
                objExpr = "(void*)this";
            }
        }

        std::string enterText = "trace_enter(" + objExpr + ", __PRETTY_FUNCTION__ ";
        // 인자 목록 추가
        for (unsigned i = 0; i < f->getNumParams(); ++i) {
            std::string name = f->getParamDecl(i)->getNameAsString();
            if (!name.empty()) {
                enterText += ", " + name;
            }
        }
        
        enterText += ");\n";
        // 함수 몸체 시작('{') 바로 다음에 삽입
        SourceLocation startLoc = body->getLBracLoc().getLocWithOffset(1);
        TheRewriter.InsertText(startLoc, enterText, true, true);

        // [2] 함수 내부 return 문 처리
        // 함수 내 return문 수집
        std::vector<ReturnStmt*> returns;
        ReturnVisitor rv(returns);
        rv.TraverseStmt(body);
        // 각 return문을 변환
        for (ReturnStmt* ret : returns) {
            std::string newText;
            SourceManager &SM = TheRewriter.getSourceMgr();  // 💡 여기 추가
            // [2] return 문 처리
            if (ret->getRetValue()) {
                std::string exprText = Lexer::getSourceText(
                    CharSourceRange::getTokenRange(ret->getRetValue()->getSourceRange()),
                    SM, TheRewriter.getLangOpts()).str();
                if (retTypeQual->isReferenceType()) {
                    newText  = "{ auto* __trace_ret = &(" + exprText + "); ";
                    newText += "trace_return(" + objExpr + ", __PRETTY_FUNCTION__, *__trace_ret); ";
                    newText += "return *__trace_ret; }";
                } else {
                    newText  = "{ auto __trace_ret = " + exprText + "; ";
                    newText += "trace_return(" + objExpr + ", __PRETTY_FUNCTION__, __trace_ret); ";
                    newText += "return __trace_ret; }";
                }
            } else {
                newText = "{ trace_return(" + objExpr + ", __PRETTY_FUNCTION__); return; }";
            }

            // 원래 return 문을 대체
            SourceLocation start = ret->getBeginLoc();
            SourceLocation end = Lexer::getLocForEndOfToken(ret->getEndLoc(), 0, SM, TheRewriter.getLangOpts());
            TheRewriter.ReplaceText(SourceRange(start, end), newText);

        }
        // [3] void 함수 끝에 암시적 반환 처리 (명시적 return이 없는 경우)
        if (returns.empty() && (retTypeQual->isVoidType() || isa<CXXConstructorDecl>(f) || isa<CXXDestructorDecl>(f))) {
            std::string endText = "\ntrace_return(" + objExpr + ", __PRETTY_FUNCTION__);\n";
            // '}' 바로 앞에 삽입
            SourceLocation endLoc = body->getRBracLoc();
            TheRewriter.InsertText(endLoc, endText, true, true);
        }

        return true;
    }
    bool VisitStmt(Stmt* stmt) {
        SourceManager &SM = TheRewriter.getSourceMgr();
    
        std::string text = Lexer::getSourceText(
            CharSourceRange::getTokenRange(stmt->getSourceRange()),
            SM, TheRewriter.getLangOpts()).str();
    
        const std::vector<std::pair<std::string, std::string>> macroRewrites = {
            {"EXPECT_EQ(",     "EXPECT_EQ_LOG("},
            {"EXPECT_NE(",     "EXPECT_NE_LOG("},
            {"EXPECT_LT(",     "EXPECT_LT_LOG("},
            {"EXPECT_LE(",     "EXPECT_LE_LOG("},
            {"EXPECT_GT(",     "EXPECT_GT_LOG("},
            {"EXPECT_GE(",     "EXPECT_GE_LOG("},
            {"EXPECT_TRUE(",   "EXPECT_TRUE_LOG("},
            {"EXPECT_FALSE(",  "EXPECT_FALSE_LOG("},
            {"EXPECT_NEAR(",   "EXPECT_NEAR_LOG("},
            {"EXPECT_STREQ(",  "EXPECT_STREQ_LOG("},
            {"ASSERT_EQ(",     "ASSERT_EQ_LOG("},
            {"ASSERT_NE(",     "ASSERT_NE_LOG("},
            {"ASSERT_LT(",     "ASSERT_LT_LOG("},
            {"ASSERT_LE(",     "ASSERT_LE_LOG("},
            {"ASSERT_GT(",     "ASSERT_GT_LOG("},
            {"ASSERT_GE(",     "ASSERT_GE_LOG("},
            {"ASSERT_TRUE(",   "ASSERT_TRUE_LOG("},
            {"ASSERT_FALSE(",  "ASSERT_FALSE_LOG("},
            {"ASSERT_NEAR(",   "ASSERT_NEAR_LOG("},
            {"ASSERT_STREQ(",  "ASSERT_STREQ_LOG("}
        };

    
        for (const auto& macro : macros) {
            if (text.find(macro) == 0) {
                // 💥 여기서 직접 trace_ofs 출력 코드로 변경
                std::string logCode =
                    "{ if(trace_ofs.is_open()) trace_ofs << \"[\" << current_test_name << \"] [ASSERTION_CALL] " + text + "\" << std::endl; }\n";
                TheRewriter.InsertText(stmt->getBeginLoc(), logCode, true, true);
                break;
            }
        }
    
        return true;
    }
    
    // bool VisitCXXRecordDecl(CXXRecordDecl *record) {
    //     if (!record->isThisDeclarationADefinition())
    //         return true;
    
    //     std::string className = record->getNameAsString();
    //     bool hasCtor = false, hasDtor = false;
    
    //     for (auto m : record->methods()) {
    //         if (isa<CXXConstructorDecl>(m)) hasCtor = true;
    //         if (isa<CXXDestructorDecl>(m)) hasDtor = true;
    //     }
    
    //     SourceManager &SM = TheRewriter.getSourceMgr();
    //     SourceLocation classEndLoc = record->getSourceRange().getEnd();
    //     SourceLocation insertLoc = Lexer::getLocForEndOfToken(
    //         classEndLoc, 0, TheRewriter.getSourceMgr(), TheRewriter.getLangOpts());
        
    //     if (!hasCtor) {
    //         std::string ctorCode = "\n" + className + "() { trace_enter((void*)this, \"" + className + "::" + className + "\"); }\n";
    //         TheRewriter.InsertText(insertLoc, ctorCode, true, true);
    //     }
        
    //     if (!hasDtor) {
    //         std::string dtorCode = "\n~" + className + "() { trace_return((void*)this, \"" + className + "::~" + className + "\"); }\n";
    //         TheRewriter.InsertText(insertLoc, dtorCode, true, true);
    //     }
        
    
    //     return true;
    // }
    
private:

    Rewriter &TheRewriter;
    std::set<std::string> VisitedFunctions;
    ASTContext &Context;

};

// ASTConsumer: 각 선언에 대해 Visitor 실행
class TraceInjectorConsumer : public ASTConsumer {
public:
    explicit TraceInjectorConsumer(Rewriter &R, ASTContext &C) : Visitor(R, C) {}
    bool HandleTopLevelDecl(DeclGroupRef DR) override {
        for (Decl* d : DR)
            Visitor.TraverseDecl(d);
        return true;
    }
private:
    TraceInjectorVisitor Visitor;
};


// FrontendAction: Rewriter 설정 및 ASTConsumer 생성, 파일 시작에 include 자동 삽입
class TraceInjectorAction : public ASTFrontendAction {
public:
    TraceInjectorAction() {}
    void EndSourceFileAction() override {
        SourceManager &SM = TheRewriter.getSourceMgr();
    
        // trace.h include는 ASTConsumer에서 이미 삽입
        // 함수 진입/종료 코드도 ASTConsumer에서 이미 삽입됨
    
        // Rewriter 버퍼 얻기
        std::string rewrittenCode;
        llvm::raw_string_ostream os(rewrittenCode);
        TheRewriter.getEditBuffer(SM.getMainFileID()).write(os);
        os.flush();
    
        // 추가 텍스트 치환 (EXPECT_, ASSERT_)
        const std::vector<std::pair<std::string, std::string>> macroRewrites = {
            {"EXPECT_EQ(",     "EXPECT_EQ_LOG("},
            {"EXPECT_NE(",     "EXPECT_NE_LOG("},
            {"EXPECT_TRUE(",   "EXPECT_TRUE_LOG("},
            {"EXPECT_FALSE(",  "EXPECT_FALSE_LOG("},
            {"EXPECT_NEAR(",   "EXPECT_NEAR_LOG("},
            {"EXPECT_STREQ(",  "EXPECT_STREQ_LOG("},
            {"ASSERT_EQ(",     "ASSERT_EQ_LOG("},
            {"ASSERT_NE(",     "ASSERT_NE_LOG("},
            {"ASSERT_TRUE(",   "ASSERT_TRUE_LOG("},
            {"ASSERT_FALSE(",  "ASSERT_FALSE_LOG("},
            {"ASSERT_NEAR(",   "ASSERT_NEAR_LOG("},
            {"ASSERT_STREQ(",  "ASSERT_STREQ_LOG("}
        };
        for (const auto& [from, to] : macroRewrites) {
            size_t pos = 0;
            while ((pos = rewrittenCode.find(from, pos)) != std::string::npos) {
                rewrittenCode.replace(pos, from.length(), to);
                pos += to.length();
            }
        }
    
        // 최종 출력
        llvm::outs() << rewrittenCode;
    }
      
    std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI, StringRef file) override {
        TheRewriter.setSourceMgr(CI.getSourceManager(), CI.getLangOpts());
        return std::make_unique<TraceInjectorConsumer>(TheRewriter, CI.getASTContext());
    }
private:
    Rewriter TheRewriter;
};

static llvm::cl::OptionCategory ToolCategory("inject-trace-tool options");

// int main(int argc, const char **argv) {
//     auto ExpectedParser = CommonOptionsParser::create(argc, argv, ToolCategory);
//     if (!ExpectedParser) {
//         llvm::errs() << ExpectedParser.takeError();
//         return 1;
//     }
//     ClangTool Tool(ExpectedParser.get().getCompilations(),
//                    ExpectedParser.get().getSourcePathList());
//     return Tool.run(newFrontendActionFactory<TraceInjectorAction>().get());
// }


// int main(int argc, const char **argv) {
//     // include 경로 직접 지정
//     std::vector<std::string> compilationFlags = {
//         "-std=c++17",
//         "-I/usr/include/c++/11",
//         "-I/usr/include/x86_64-linux-gnu/c++/11",
//         "-I/usr/include/c++/11/backward",
//         "-I/usr/lib/llvm-18/lib/clang/18/include",
//         "-I/usr/local/include",
//         "-I/usr/include/x86_64-linux-gnu",
//         "-I/usr/include",
//         "-I/usr/include/gtest",
//         "-Itests"
//     };

//     clang::tooling::FixedCompilationDatabase CompilDB(".", compilationFlags);

//     clang::tooling::ClangTool Tool(CompilDB, llvm::ArrayRef<std::string>(argv + 1, argv + argc));
    
//     return Tool.run(clang::tooling::newFrontendActionFactory<YourFrontendAction>().get());
// }

int main(int argc, const char **argv) {
    std::vector<std::string> compilationFlags = {
        "-x", "c++",
        "-std=c++17",
        "-I/usr/include/c++/11",
        "-I/usr/include/x86_64-linux-gnu/c++/11",
        "-I/usr/include/c++/11/backward",
        "-I/usr/lib/llvm-18/lib/clang/18/include",
        "-I/usr/local/include",
        "-I/usr/include/x86_64-linux-gnu",
        "-I/usr/include",
        "-I/usr/include/gtest",
        "-Itests"
    };

    FixedCompilationDatabase CompilDB(".", compilationFlags);

    std::vector<std::string> sourcePaths;
    for (int i = 1; i < argc; ++i) {
        std::string arg(argv[i]);
        // 옵션이 아닌 파일만 수집
        if (arg.compare(0, 1, "-") != 0)
            sourcePaths.push_back(arg);
    }

    ClangTool Tool(CompilDB, sourcePaths);
    return Tool.run(newFrontendActionFactory<TraceInjectorAction>().get());
}
