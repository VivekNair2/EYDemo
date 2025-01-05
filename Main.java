
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter the name ");
        String name = scanner.nextLine();
        System.out.println("Hello, " + name + "!");
        
    }
}


 class Animal{
    public void makeSound(){
        System.out.println("Animal makes a sound");
    }
}