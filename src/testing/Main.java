package testing;
import additionalClasses.Matrix;
import data.Set;
import recurrentNeuralNetwork.lstmNetwork.*;
import recurrentNeuralNetwork.training.Trainer;

import java.util.ArrayList;

/**
 * Created by arseny on 23.03.17.
 */
public class Main {
    public static void main(String[] args) {

        Set data = new XORdata();
        ArrayList<Layer> layers = new ArrayList<>();
        Network lstm = new Network(layers);
        lstm = lstm.makeLSTM(data.getInputDim(),3, 4);

        int epoch = 1_000;
        double learningRate = 0.0001;

        double loss = Trainer.train(epoch, learningRate, lstm, data);
        System.out.println("Loss value: " + loss);

        System.out.println("Training completed");
        System.out.println("Test: 1, 1");
        Matrix input = new Matrix(new double[] {1,1});
        Matrix output = lstm.activate(input);
        System.out.println("Test: 1, 1. Output: " + output.getArrayElem(0));
        System.out.println("Waiting for 0");

        System.out.println("Test: 0, 1");
        input = new Matrix(new double[] {0,1});
        output = lstm.activate(input);
        System.out.println("Test: 0, 1. Output: " + output.getArrayElem(0));
        System.out.println("Waiting for 1");

        System.out.println("DONE");
    }

}