#include <iostream>
#include <vector>
#include <string>

#include "clang/AST/AST.h"
#include "clang/ASTMatchers/ASTMatchFinder.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CompilationDatabase.h"

using namespace clang;
using namespace clang::ast_matchers;
using namespace clang::tooling;

class FunctionPrinter : public MatchFinder::MatchCallback {
public:
  void run(const MatchFinder::MatchResult &Result) override {
    if (const FunctionDecl *FD = Result.Nodes.getNodeAs<FunctionDecl>("func")) {
      if (FD->hasBody()) {
        llvm::outs() << "Function: " << FD->getNameInfo().getName().getAsString() << "\n";
      }
    }
  }
};

int main(int argc, const char **argv) {
  // 인자: -std=c++17 -I../src -I/usr/include/gtest
  std::vector<std::string> compileArgs;
  for (int i = 1; i < argc; ++i) {
    compileArgs.emplace_back(argv[i]);
  }

  FixedCompilationDatabase Compilations(".", compileArgs);
  std::vector<std::string> SourcePaths = {"../src/sample3_unittest.cc"};

  ClangTool Tool(Compilations, SourcePaths);

  FunctionPrinter Printer;
  MatchFinder Finder;
  Finder.addMatcher(functionDecl(isDefinition()).bind("func"), &Printer);

  return Tool.run(newFrontendActionFactory(&Finder).get());
}
